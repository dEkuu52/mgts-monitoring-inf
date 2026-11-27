"""Бизнес-логика дефектов."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.defect import Defect
from app.models.infrastructure_object import InfrastructureObject
from app.schemas.defect import DefectCreate, DefectUpdate


async def list_defects(session: AsyncSession) -> list[Defect]:
    result = await session.scalars(select(Defect).order_by(Defect.id))
    return list(result)


async def get_defect(session: AsyncSession, defect_id: int) -> Defect:
    defect = await session.get(Defect, defect_id)
    if defect is None:
        raise AppError(404, "Дефект не найден", f"Дефект с id={defect_id} не существует.")
    return defect


async def create_defect(session: AsyncSession, payload: DefectCreate) -> Defect:
    await _ensure_object_exists(session, payload.object_id)

    defect = Defect(**payload.model_dump())
    session.add(defect)
    await session.commit()
    await session.refresh(defect)
    return defect


async def update_defect(session: AsyncSession, defect_id: int, payload: DefectUpdate) -> Defect:
    defect = await get_defect(session, defect_id)
    changes = payload.model_dump(exclude_unset=True)

    if "object_id" in changes:
        await _ensure_object_exists(session, changes["object_id"])

    for field, value in changes.items():
        setattr(defect, field, value)

    await session.commit()
    await session.refresh(defect)
    return defect


async def delete_defect(session: AsyncSession, defect_id: int) -> None:
    defect = await get_defect(session, defect_id)
    await session.delete(defect)
    await session.commit()


async def _ensure_object_exists(session: AsyncSession, object_id: int | None) -> None:
    if object_id is None:
        return
    if await session.get(InfrastructureObject, object_id) is None:
        raise AppError(400, "Объект не найден", f"Нельзя привязать дефект к объекту id={object_id}.")
