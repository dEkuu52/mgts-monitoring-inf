"""Общие константы и утилиты очереди обработки фото ИИ-воркером.

Единый источник правды и для API (которое ставит статус ``awaiting_processing``
при загрузке фото), и для воркера (который этот статус забирает).
"""

from __future__ import annotations

from pathlib import Path

# Статусы колонки infrastructure_objects.processing_status.
STATUS_AWAITING = "awaiting_processing"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

# Ошибочное написание из ТЗ и старое значение из первого варианта воркера
# тоже понимаем как «в очереди», чтобы старые записи не зависали.
AWAITING_STATUSES = (STATUS_AWAITING, "awating_processing", "pending")

# Обработанные (аннотированные) картинки отдаются тем же static-монтом /uploads.
PROCESSED_PREFIX = "/uploads/processed/"


def processed_path(url: str | None, uploads_dir: Path) -> Path | None:
    """Безопасный путь к обработанному фото по его публичному URL.

    Возвращает ``None`` для любого чуждого/некорректного значения: пользователь
    может прислать что угодно, а воркер не должен удалять файлы вне папки
    ``uploads/processed``.
    """
    if not isinstance(url, str) or not url.startswith(PROCESSED_PREFIX):
        return None
    root = (uploads_dir / "processed").resolve()
    path = (uploads_dir / url.removeprefix("/uploads/")).resolve()
    if not path.is_relative_to(root):
        return None
    return path


def remove_processed_image(url: str | None, uploads_dir: Path) -> None:
    """Удаляет старое обработанное фото (best-effort)."""
    path = processed_path(url, uploads_dir)
    if path is not None:
        path.unlink(missing_ok=True)
