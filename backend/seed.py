"""Демонстрационные данные для локальной разработки.

Запуск из папки `backend`:

    .venv\\Scripts\\python.exe seed.py

Скрипт идемпотентный: существующие записи не дублируются.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import SessionLocal, dispose_engine
from app.models import Defect, InfrastructureObject, Status, User

DEMO_USERS = [
    {"username": "admin", "email": "admin@mgts.ru", "phone": "+7 495 000-00-03", "role": "admin", "password": "admin123"},
    {"username": "operator", "email": "operator@mgts.ru", "phone": "+7 495 000-00-01", "role": "operator", "password": "operator123"},
    {"username": "engineer", "email": "engineer@mgts.ru", "phone": "+7 495 000-00-02", "role": "engineer", "password": "engineer123"},
]

DEMO_STATUSES = [
    {"type": "ok", "description": "Объект в нормативном состоянии"},
    {"type": "check_required", "description": "Требуется проверка"},
    {"type": "repair_required", "description": "Требуется ремонт"},
    {"type": "unrecognized", "description": "Не распознано"},
]

DEMO_OBJECTS = [
    {
        "external_id": "МГТС-КЛ-0001",
        "type": "cable_manhole",
        "place": "Москва, ул. Хамовнический Вал, 5",
        "lat": 55.7279,
        "lon": 37.5686,
        "status_type": "check_required",
    },
    {
        "external_id": "МГТС-ОП-0142",
        "type": "support",
        "place": "Москва, Комсомольский просп., 28",
        "lat": 55.7274,
        "lon": 37.5831,
        "status_type": "ok",
    },
    {
        "external_id": "МГТС-КЛ-0007",
        "type": "cable_manhole",
        "place": "Москва, ул. Льва Толстого, 14",
        "lat": 55.7338,
        "lon": 37.5882,
        "status_type": "repair_required",
    },
    {
        "external_id": "МГТС-ШК-0031",
        "type": "cabinet",
        "place": "Москва, Фрунзенская наб., 12",
        "lat": 55.7271,
        "lon": 37.5934,
        "status_type": "ok",
    },
    {
        "external_id": "МГТС-ОП-0157",
        "type": "support",
        "place": "Москва, ул. Усачёва, 11",
        "lat": 55.7297,
        "lon": 37.5672,
        "status_type": "check_required",
    },
]

DEMO_DEFECTS = [
    {
        "external_id": "МГТС-КЛ-0001",
        "detection_id": 501,
        "defect_type": "cover_displaced",
        "defect_confidence": 0.84,
        "severity": "high",
        "recommended_action": "check",
    },
    {
        "external_id": "МГТС-ОП-0142",
        "detection_id": 502,
        "defect_type": "support_tilted",
        "defect_confidence": 0.71,
        "severity": "medium",
        "recommended_action": "check",
    },
    {
        "external_id": "МГТС-КЛ-0007",
        "detection_id": 503,
        "defect_type": "cover_missing",
        "defect_confidence": 0.88,
        "severity": "high",
        "recommended_action": "repair",
    },
    {
        "external_id": "МГТС-ШК-0031",
        "detection_id": 504,
        "defect_type": "cabinet_door_open",
        "defect_confidence": 0.62,
        "severity": "medium",
        "recommended_action": "check",
    },
]


async def _get_or_create(
    session: AsyncSession,
    model,
    lookup: dict,
    values: dict | None = None,
):
    """Возвращает запись по уникальным полям, создавая её при необходимости."""
    statement = select(model).filter_by(**lookup)
    existing = (await session.scalars(statement)).first()
    if existing is not None:
        return existing, False

    obj = model(**lookup, **(values or {}))
    session.add(obj)
    await session.flush()
    return obj, True


async def seed() -> None:
    async with SessionLocal() as session:
        for data in DEMO_STATUSES:
            await _get_or_create(
                session,
                Status,
                lookup={"type": data["type"]},
                values={"description": data["description"]},
            )
        await session.flush()

        statuses = {
            status.type: status
            for status in (await session.scalars(select(Status))).all()
        }

        for data in DEMO_USERS:
            await _get_or_create(
                session,
                User,
                lookup={"username": data["username"]},
                values={
                    "email": data["email"],
                    "phone": data["phone"],
                    "role": data["role"],
                    "password_hash": hash_password(data["password"]),
                },
            )

        objects: dict[str, InfrastructureObject] = {}
        for data in DEMO_OBJECTS:
            obj, _ = await _get_or_create(
                session,
                InfrastructureObject,
                lookup={"external_id": data["external_id"]},
                values={
                    "type": data["type"],
                    "place": data["place"],
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "status_id": statuses[data["status_type"]].id,
                },
            )
            objects[data["external_id"]] = obj

        await session.flush()

        existing_defects = await session.scalar(select(Defect.id).limit(1))
        if existing_defects is None:
            for data in DEMO_DEFECTS:
                session.add(
                    Defect(
                        object_id=objects[data["external_id"]].id,
                        detection_id=data["detection_id"],
                        defect_type=data["defect_type"],
                        defect_confidence=data["defect_confidence"],
                        severity=data["severity"],
                        recommended_action=data["recommended_action"],
                    )
                )

        await session.commit()

    await dispose_engine()
    print("Демо-данные готовы. Вход: admin / admin123, operator / operator123, engineer / engineer123")


if __name__ == "__main__":
    asyncio.run(seed())
