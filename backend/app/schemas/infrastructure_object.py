from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import blank_to_none


class InfrastructureObjectBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: str | None = Field(default=None, max_length=100)
    external_id: str | None = Field(default=None, max_length=100)
    place: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    status_id: int | None = None

    @field_validator("type", "external_id", "place", "lat", "lon", "status_id", mode="before")
    @classmethod
    def _normalize_empty(cls, value: object) -> object:
        # Поля формы приходят строками, пустое значение означает null.
        return blank_to_none(value)


class InfrastructureObjectCreate(InfrastructureObjectBase):
    pass


class InfrastructureObjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: str | None = Field(default=None, max_length=100)
    external_id: str | None = Field(default=None, max_length=100)
    place: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    status_id: int | None = None

    @field_validator("type", "external_id", "place", "lat", "lon", "status_id", mode="before")
    @classmethod
    def _normalize_empty(cls, value: object) -> object:
        return blank_to_none(value)


class InfrastructureObjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str | None
    external_id: str | None
    place: str | None
    lat: float | None
    lon: float | None
    status_id: int | None
    img_url: str | None
    # Поля воркера/ИИ. Необязательные: на ветке с фото объектов эти колонки
    # ещё не появились в БД, и старые ответы API их не содержат.
    processed_img_url: str | None = None
    processing_status: str | None = None
    processing_error: str | None = None
    processed_at: datetime | None = None
