"""Бизнес-логика объектов инфраструктуры."""

from __future__ import annotations

from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.core.config import settings
from app.core.errors import AppError
from app.core.processing import STATUS_AWAITING, remove_processed_image
from app.models.defect import Defect
from app.models.infrastructure_object import PHOTO_KEY_PREFIX, InfrastructureObject
from app.models.status import Status
from app.schemas.infrastructure_object import (
    InfrastructureObjectCreate,
    InfrastructureObjectUpdate,
)

_IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_READ_CHUNK_SIZE = 64 * 1024


async def list_objects(session: AsyncSession) -> list[InfrastructureObject]:
    result = await session.scalars(
        select(InfrastructureObject).order_by(InfrastructureObject.id)
    )
    return list(result)


async def get_object(session: AsyncSession, object_id: int) -> InfrastructureObject:
    obj = await session.get(InfrastructureObject, object_id)
    if obj is None:
        raise AppError(404, "Объект не найден", f"Объект с id={object_id} не существует.")
    return obj


async def create_object(
    session: AsyncSession,
    payload: InfrastructureObjectCreate,
) -> InfrastructureObject:
    await _ensure_status_exists(session, payload.status_id)

    obj = InfrastructureObject(**payload.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def update_object(
    session: AsyncSession,
    object_id: int,
    payload: InfrastructureObjectUpdate,
) -> InfrastructureObject:
    obj = await get_object(session, object_id)
    changes = payload.model_dump(exclude_unset=True)

    if "status_id" in changes:
        await _ensure_status_exists(session, changes["status_id"])

    for field, value in changes.items():
        setattr(obj, field, value)

    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_object(session: AsyncSession, object_id: int) -> None:
    obj = await get_object(session, object_id)
    photo_key = obj.img_key
    processed_url = obj.processed_img_url
    await session.execute(
        delete(Defect).where(Defect.object_id == object_id, Defect.source == "cv")
    )
    await session.delete(obj)
    await session.commit()

    if _is_managed_photo(photo_key):
        await storage.delete_object(photo_key)
    remove_processed_image(processed_url, settings.uploads_path)


async def set_object_photo(
    session: AsyncSession,
    object_id: int,
    upload: UploadFile,
) -> InfrastructureObject:
    """Загружает фото объекта в MinIO и сохраняет ключ в БД."""
    obj = await get_object(session, object_id)
    data = await _read_photo(upload)

    content_type = _detect_image_type(data)
    if content_type is None:
        raise AppError(
            415,
            "Неподдерживаемый формат",
            "Допустимы изображения JPEG, PNG и WebP.",
        )

    key = _photo_key(obj.id, content_type)
    await storage.put_object(key, data, content_type)

    old_key = obj.img_key
    old_processed_url = obj.processed_img_url

    obj.img_key = key
    # Новый файл попадает в очередь ИИ. Старые результаты больше не актуальны.
    obj.processing_status = STATUS_AWAITING
    obj.processing_started_at = None
    obj.processing_attempts = 0
    obj.processing_error = None
    obj.processed_at = None
    obj.processed_img_url = None

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        # Файл уже загружен, но БД его не знает — убираем, чтобы не копить мусор.
        await storage.delete_object(key)
        raise
    await session.refresh(obj)

    if _is_managed_photo(old_key) and old_key != key:
        await storage.delete_object(old_key)
    remove_processed_image(old_processed_url, settings.uploads_path)

    return obj


async def get_object_photo(
    session: AsyncSession,
    object_id: int,
) -> tuple[bytes, str]:
    obj = await get_object(session, object_id)
    key = obj.img_key
    if not _is_managed_photo(key):
        raise AppError(404, "Фото не найдено", f"У объекта id={object_id} нет загруженного фото.")
    return await storage.get_object(key)


async def remove_object_photo(
    session: AsyncSession,
    object_id: int,
) -> InfrastructureObject:
    obj = await get_object(session, object_id)
    key = obj.img_key
    processed_url = obj.processed_img_url

    # Результаты обработки больше не соответствуют объекту даже если фото уже не было.
    await session.execute(
        delete(Defect).where(Defect.object_id == object_id, Defect.source == "cv")
    )
    obj.processing_status = None
    obj.processing_started_at = None
    obj.processing_attempts = 0
    obj.processing_error = None
    obj.processed_at = None
    obj.processed_img_url = None

    if key is not None:
        obj.img_key = None
    await session.commit()
    await session.refresh(obj)

    if _is_managed_photo(key):
        await storage.delete_object(key)
    remove_processed_image(processed_url, settings.uploads_path)

    return obj


async def _read_photo(upload: UploadFile) -> bytes:
    limit = settings.max_photo_size_bytes
    chunks: list[bytes] = []
    total = 0

    while chunk := await upload.read(_READ_CHUNK_SIZE):
        total += len(chunk)
        if total > limit:
            raise AppError(
                413,
                "Файл слишком большой",
                f"Максимальный размер фото — {settings.max_photo_size_mb} МБ.",
            )
        chunks.append(chunk)

    if total == 0:
        raise AppError(400, "Пустой файл", "Загрузите изображение.")

    return b"".join(chunks)


def _detect_image_type(data: bytes) -> str | None:
    """Определяет формат по сигнатуре файла, а не по доверенному content-type."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _photo_key(object_id: int, content_type: str) -> str:
    return f"{PHOTO_KEY_PREFIX}{object_id}/{uuid4().hex}{_IMAGE_EXTENSIONS[content_type]}"


def _is_managed_photo(key: str | None) -> bool:
    """True для ключей, которые создал API (их можно удалять из S3)."""
    return bool(key) and key.startswith(PHOTO_KEY_PREFIX)


async def _ensure_status_exists(session: AsyncSession, status_id: int | None) -> None:
    if status_id is None:
        return
    if await session.get(Status, status_id) is None:
        raise AppError(400, "Статус не найден", f"Нельзя указать несуществующий статус id={status_id}.")
