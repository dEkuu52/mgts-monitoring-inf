from __future__ import annotations

import asyncio
import logging
import signal
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import cv2
from sqlalchemy import case, delete, func, select, update
from ultralytics import YOLO

from app.core import storage
from app.core.config import settings
from app.core.errors import AppError
from app.core.processing import (
    AWAITING_STATUSES,
    PROCESSED_PREFIX,
    STATUS_AWAITING,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_PROCESSING,
    remove_processed_image,
)
from app.db.session import SessionLocal, dispose_engine
from app.models import Defect, InfrastructureObject as Obj, Status
from app.models.infrastructure_object import PHOTO_KEY_PREFIX
from app.services.cv_logic import (
    CLASS_RULES,
    REQUIRED_STATUSES,
    Detection,
    Outcome,
    build_outcome,
    condition_is_assessed,
    gps_from_image,
    resolve_image_path,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("worker")

REQUEUE_EVERY_SECONDS = 60
# Расширение файла, который скачиваем из MinIO, если content-type не распознан.
_EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass(frozen=True)
class Job:
    id: int
    img_key: str
    attempts: int  # уже с учётом текущей попытки
    old_processed_url: str | None


def processed_dir() -> Path:
    return settings.uploads_path / "processed"


# ---------------------------------------------------------------------------
# Инференс (синхронный, вызывается через asyncio.to_thread).
# ---------------------------------------------------------------------------
def analyze_image(
    model: YOLO,
    source: Path,
    save_path: Path,
) -> tuple[list[Detection], tuple[float, float] | None]:
    results = model.predict(
        source=str(source),
        imgsz=settings.cv_imgsz,
        conf=settings.cv_min_confidence,
        iou=settings.cv_iou,
        verbose=False,
    )
    result = results[0]

    detections: list[Detection] = []
    boxes = result.boxes
    if boxes is not None and len(boxes) > 0:
        for bbox, conf, cls in zip(
            boxes.xyxyn.tolist(), boxes.conf.tolist(), boxes.cls.tolist()
        ):
            detections.append(
                Detection(
                    class_name=str(model.names[int(cls)]),
                    confidence=round(float(conf), 4),
                    bbox=tuple(round(float(v), 4) for v in bbox),  # type: ignore[arg-type]
                )
            )

    if not cv2.imwrite(str(save_path), result.plot()):
        raise RuntimeError(f"Не удалось сохранить обработанное фото: {save_path}")

    return detections, gps_from_image(source)


async def prepare_source(job: Job, tmp_dir: Path) -> Path:
    """Достаёт исходное фото: из MinIO по ключу или с диска (старый /uploads/raw)."""
    key = job.img_key or ""
    if key.startswith(PHOTO_KEY_PREFIX):
        data, content_type = await storage.get_object(key)
        ext = _EXT_BY_CONTENT_TYPE.get(content_type) or Path(key).suffix or ".jpg"
        path = tmp_dir / f"source_{job.id}{ext}"
        path.write_bytes(data)
        return path

    if key.startswith("/uploads/raw/"):
        return resolve_image_path(key, settings.uploads_path)

    raise ValueError(
        f"Объект ID={job.id}: неподдерживаемое значение imgUrl {key!r} "
        f"(ожидается ключ '{PHOTO_KEY_PREFIX}...' или '/uploads/raw/...')"
    )


# ---------------------------------------------------------------------------
# Работа с БД.
# ---------------------------------------------------------------------------
async def get_status_map() -> dict[str, int]:
    async with SessionLocal() as session:
        statuses = (await session.scalars(select(Status))).all()
    return {s.type: s.id for s in statuses}


async def claim_next() -> Job | None:
    """Атомарно берёт один объект из очереди, выставляя статус processing."""
    next_id = (
        select(Obj.id)
        .where(
            Obj.processing_status.in_(AWAITING_STATUSES),
            Obj.img_key.is_not(None),
            Obj.img_key != "",
        )
        .order_by(Obj.id)
        .limit(1)
        .with_for_update(skip_locked=True)
        .scalar_subquery()
    )
    stmt = (
        update(Obj)
        .where(Obj.id == next_id, Obj.processing_status.in_(AWAITING_STATUSES))
        .values(
            processing_status=STATUS_PROCESSING,
            processing_started_at=func.now(),
            processing_attempts=Obj.processing_attempts + 1,
            processing_error=None,
        )
        .returning(Obj.id, Obj.img_key, Obj.processing_attempts, Obj.processed_img_url)
        .execution_options(synchronize_session=False)
    )
    async with SessionLocal() as session:
        row = (await session.execute(stmt)).first()
        await session.commit()

    if row is None:
        return None
    return Job(id=row[0], img_key=row[1], attempts=row[2], old_processed_url=row[3])


async def requeue_stale() -> int:
    """Возвращает в очередь объекты, зависшие в статусе processing."""
    threshold = func.now() - timedelta(minutes=settings.worker_stale_minutes)
    stmt = (
        update(Obj)
        .where(
            Obj.processing_status == STATUS_PROCESSING,
            Obj.processing_started_at < threshold,
        )
        .values(
            processing_status=case(
                (Obj.processing_attempts >= settings.worker_max_attempts, STATUS_FAILED),
                else_=STATUS_AWAITING,
            ),
            processing_error="Обработка прервана (таймаут воркера)",
        )
        .returning(Obj.id)
        .execution_options(synchronize_session=False)
    )
    async with SessionLocal() as session:
        rows = (await session.execute(stmt)).all()
        await session.commit()
    return len(rows)


async def save_result(
    job: Job,
    outcome: Outcome,
    processed_url: str,
    gps: tuple[float, float] | None,
    status_map: dict[str, int],
) -> None:
    async with SessionLocal() as session:
        # Дефекты воркера пересоздаём при каждой повторной обработке фото,
        # а ручные записи (source='manual') не трогаем.
        await session.execute(
            delete(Defect).where(Defect.object_id == job.id, Defect.source == "cv")
        )
        for item in outcome.defects:
            session.add(
                Defect(
                    object_id=job.id,
                    defect_type=item.defect_type,
                    defect_confidence=item.confidence,
                    severity=item.severity,
                    recommended_action=item.action,
                    bbox=list(item.bbox),
                    source="cv",
                )
            )

        values: dict = {
            "processing_status": STATUS_DONE,
            "processed_at": func.now(),
            "processing_error": None,
            "processed_img_url": processed_url,
        }
        if outcome.status and outcome.status in status_map:
            values["status_id"] = status_map[outcome.status]
        await session.execute(
            update(Obj)
            .where(Obj.id == job.id)
            .values(**values)
            .execution_options(synchronize_session=False)
        )

        if outcome.object_type:
            await session.execute(
                update(Obj)
                .where(Obj.id == job.id, Obj.type.is_(None))
                .values(type=outcome.object_type)
                .execution_options(synchronize_session=False)
            )
        if gps:
            await session.execute(
                update(Obj)
                .where(Obj.id == job.id, Obj.lat.is_(None), Obj.lon.is_(None))
                .values(lat=gps[0], lon=gps[1])
                .execution_options(synchronize_session=False)
            )

        await session.commit()


async def mark_failed(job: Job, message: str, *, permanent: bool) -> None:
    give_up = permanent or job.attempts >= settings.worker_max_attempts
    async with SessionLocal() as session:
        await session.execute(
            update(Obj)
            .where(Obj.id == job.id)
            .values(
                processing_status=STATUS_FAILED if give_up else STATUS_AWAITING,
                processing_error=message[:1000],
            )
            .execution_options(synchronize_session=False)
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Обработка одного объекта.
# ---------------------------------------------------------------------------
async def handle_job(job: Job, model: YOLO, status_map: dict[str, int]) -> None:
    started = time.perf_counter()
    logger.info("Взял в работу объект ID=%s (попытка %s): %s", job.id, job.attempts, job.img_key)

    with tempfile.TemporaryDirectory(prefix="mgts-cv-") as tmp:
        tmp_dir = Path(tmp)
        try:
            source = await prepare_source(job, tmp_dir)
            save_name = f"obj_{job.id}_{uuid.uuid4().hex[:8]}.jpg"
            processed_dir().mkdir(parents=True, exist_ok=True)
            save_path = processed_dir() / save_name

            detections, gps = await asyncio.to_thread(analyze_image, model, source, save_path)
            outcome = build_outcome(detections, high_confidence=settings.cv_high_confidence)
            await save_result(job, outcome, f"{PROCESSED_PREFIX}{save_name}", gps, status_map)
        except (ValueError, FileNotFoundError) as exc:
            logger.error("Объект ID=%s отклонён: %s", job.id, exc)
            await mark_failed(job, f"{type(exc).__name__}: {exc}", permanent=True)
            return
        except AppError as exc:
            # 503 от MinIO — временная проблема, попробуем ещё раз; 404 — нет смысла.
            retryable = exc.status_code >= 500
            logger.error(
                "Объект ID=%s: ошибка хранилища (%s): %s", job.id, exc.status_code, exc
            )
            await mark_failed(job, f"{type(exc).__name__}: {exc}", permanent=not retryable)
            return
        except Exception as exc:
            logger.exception("Ошибка при обработке объекта ID=%s", job.id)
            await mark_failed(job, f"{type(exc).__name__}: {exc}", permanent=False)
            return

    # Успешно обработали — предыдущая аннотированная картинка не нужна.
    remove_processed_image(job.old_processed_url, settings.uploads_path)
    logger.info(
        "Готово ID=%s за %.2f с: %s%s",
        job.id,
        time.perf_counter() - started,
        outcome.summary,
        f", координаты из EXIF: {gps}" if gps else "",
    )


# ---------------------------------------------------------------------------
# Главный цикл.
# ---------------------------------------------------------------------------
async def sleep_or_stop(stop: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), timeout=seconds)
    except asyncio.TimeoutError:
        pass


def log_model_info(model: YOLO) -> None:
    names = dict(model.names)
    logger.info("Классы модели: %s", names)
    for name in names.values():
        if name not in CLASS_RULES:
            logger.warning(
                "Класс '%s' не описан в CLASS_RULES (app/services/cv_logic.py) — "
                "будет считаться дефектом средней серьёзности.",
                name,
            )
    if not condition_is_assessed():
        logger.warning(
            "В CLASS_RULES нет классов-дефектов: модель только опознаёт объекты и не оценивает "
            "их состояние, поэтому опознанные объекты получают статус check_required."
        )


async def run_worker() -> None:
    weights = settings.weights_file
    if not weights.is_file():
        logger.error("Файл весов модели не найден: %s (задайте WEIGHTS_PATH)", weights)
        sys.exit(1)

    processed_dir().mkdir(parents=True, exist_ok=True)

    logger.info("Загружаю модель YOLO из %s...", weights)
    model = await asyncio.to_thread(YOLO, str(weights))
    log_model_info(model)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError):  # Windows
            pass

    logger.info("Воркер запущен и ждёт объекты со статусом %s...", STATUS_AWAITING)
    last_requeue = 0.0
    warned_statuses = False

    try:
        while not stop.is_set():
            try:
                if time.monotonic() - last_requeue >= REQUEUE_EVERY_SECONDS:
                    last_requeue = time.monotonic()
                    returned = await requeue_stale()
                    if returned:
                        logger.warning("Возвращено в очередь зависших объектов: %d", returned)

                status_map = await get_status_map()
                missing = [s for s in REQUIRED_STATUSES if s not in status_map]
                if missing:
                    if not warned_statuses:
                        logger.warning(
                            "В таблице statuses нет: %s. Жду (запустите seed.py).",
                            ", ".join(missing),
                        )
                        warned_statuses = True
                    await sleep_or_stop(stop, 5)
                    continue
                warned_statuses = False

                job = await claim_next()
                if job is None:
                    await sleep_or_stop(stop, settings.worker_poll_interval)
                    continue
                await handle_job(job, model, status_map)
            except Exception:
                logger.exception("Ошибка в цикле воркера")
                await sleep_or_stop(stop, 5)
    finally:
        logger.info("Воркер останавливается")
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(run_worker())
