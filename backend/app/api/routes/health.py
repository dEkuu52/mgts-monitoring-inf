import logging

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import SessionDep
from app.core.errors import AppError
from app.core.responses import ok
from app.schemas.common import Envelope

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Система"])


@router.get("/health", response_model=Envelope[dict[str, str]])
async def health(session: SessionDep):
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — healthcheck не должен падать трейсбеком
        logger.error("Проверка БД не прошла: %s", exc)
        raise AppError(503, "Сервис недоступен", "Нет соединения с базой данных.")

    return ok({"status": "ok", "database": "ok", "version": __version__})
