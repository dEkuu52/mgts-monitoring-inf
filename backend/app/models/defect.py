from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Defect(Base):
    """Признак дефекта, найденный на кадре (результат работы воркера/ИИ)."""

    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    object_id: Mapped[int | None] = mapped_column(
        ForeignKey("infrastructure_objects.id", ondelete="SET NULL"),
    )
    detection_id: Mapped[int | None] = mapped_column(Integer)
    defect_type: Mapped[str] = mapped_column(String(100), nullable=False)
    defect_confidence: Mapped[float | None] = mapped_column(Float)
    severity: Mapped[str | None] = mapped_column(String(50))
    recommended_action: Mapped[str | None] = mapped_column(String(50))
    # Рамка на исходном фото: [x1, y1, x2, y2], координаты нормированы 0..1.
    bbox: Mapped[list[float] | None] = mapped_column(JSONB)
    # Кто создал запись: 'cv' — воркер (пересоздаётся при повторной обработке), 'manual' — человек.
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual", server_default="manual")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
