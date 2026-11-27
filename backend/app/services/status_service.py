"""Бизнес-логика статусов."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.status import Status
from app.schemas.status import StatusCreate, StatusUpdate


async def list_statuses(session: AsyncSession) -> list[Status]:
    result = await session.scalars(select(Status).order_by(Status.id))
    return list(result)


async def get_status(session: AsyncSession, status_id: int) -> Status:
    status = await session.get(Status, status_id)
    if status is None:
        raise AppError(404, "Статус не найден", f"Статус с id={status_id} не существует.")
    return status


async def create_status(session: AsyncSession, payload: StatusCreate) -> Status:
    status = Status(type=payload.type, description=payload.description)
    session.add(status)
    await session.commit()
    await session.refresh(status)
    return status


async def update_status(session: AsyncSession, status_id: int, payload: StatusUpdate) -> Status:
    status = await get_status(session, status_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(status, field, value)
    await session.commit()
    await session.refresh(status)
    return status


async def delete_status(session: AsyncSession, status_id: int) -> None:
    status = await get_status(session, status_id)
    await session.delete(status)
    await session.commit()
