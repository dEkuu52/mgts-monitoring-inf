from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.base import Base

# Ключи фото, которыми управляет API, лежат в этом префиксе bucket.
PHOTO_KEY_PREFIX = "objects/"


class InfrastructureObject(Base):
    __tablename__ = "infrastructure_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Имена колонок в исходной схеме заданы в camelCase.
    # В "imgUrl" хранится ключ файла в S3, а не готовая ссылка.
    img_key: Mapped[str | None] = mapped_column("imgUrl", Text)
    type: Mapped[str | None] = mapped_column(String(100))
    status_id: Mapped[int | None] = mapped_column(
        "statusId",
        ForeignKey("statuses.id", ondelete="SET NULL"),
    )
    place: Mapped[str | None] = mapped_column(Text)

    # Дополнительные поля инфраструктурного объекта из backend/sql/schema.sql.
    external_id: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)

    # Очередь обработки ИИ. Заполняется API при загрузке фото и воркером.
    processing_status: Mapped[str | None] = mapped_column(String(32))
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    processing_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    processing_error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Публичный URL аннотированного фото: /uploads/processed/<file>.jpg
    processed_img_url: Mapped[str | None] = mapped_column(Text)

    @property
    def img_url(self) -> str | None:
        """Ссылка для клиента: API-эндпоинт фото или внешний URL из старых данных."""
        if not self.img_key:
            return None
        if not self.img_key.startswith(PHOTO_KEY_PREFIX):
            return self.img_key
        if self.id is None:
            return None
        return f"{settings.api_prefix}/infrastructure-objects/{self.id}/photo"
