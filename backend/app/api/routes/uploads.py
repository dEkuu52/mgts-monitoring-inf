import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.core.config import settings
from app.core.errors import AppError
from app.core.responses import ok

router = APIRouter(tags=["Загрузка файлов"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _looks_like_image(head: bytes, ext: str) -> bool:
    """Проверка по сигнатуре файла: расширение легко подделать."""
    if ext in {".jpg", ".jpeg"}:
        return head.startswith(b"\xff\xd8\xff")
    if ext == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    return False


@router.post("/upload")
async def upload_photo(file: UploadFile = File(...)):
    if not file.filename:
        raise AppError(400, "Ошибка файла", "Имя файла не передано.")

    ext = Path(file.filename).suffix.lower() or ".jpg"
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(400, "Неверный формат", "Разрешены только JPG, PNG и WEBP.")

    limit = settings.max_upload_mb * 1024 * 1024
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise AppError(413, "Файл слишком большой", f"Максимальный размер — {settings.max_upload_mb} МБ.")
    if not _looks_like_image(content[:12], ext):
        raise AppError(400, "Неверный формат", "Содержимое файла не похоже на изображение.")

    raw_dir = settings.uploads_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    (raw_dir / filename).write_bytes(content)

    return ok({"img_url": f"/uploads/raw/{filename}"})
