from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import blank_to_none


class DefectBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    detection_id: int | None = None
    defect_type: str = Field(min_length=1, max_length=100)
    defect_confidence: float | None = Field(default=None, ge=0, le=1)
    severity: str | None = Field(default=None, max_length=50)
    recommended_action: str | None = Field(default=None, max_length=50)
    object_id: int | None = None

    @field_validator("detection_id", "defect_confidence", "severity", "recommended_action", "object_id", mode="before")
    @classmethod
    def _normalize_empty(cls, value: object) -> object:
        return blank_to_none(value)


class DefectCreate(DefectBase):
    pass


class DefectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    detection_id: int | None = None
    defect_type: str | None = Field(default=None, min_length=1, max_length=100)
    defect_confidence: float | None = Field(default=None, ge=0, le=1)
    severity: str | None = Field(default=None, max_length=50)
    recommended_action: str | None = Field(default=None, max_length=50)
    object_id: int | None = None

    @field_validator("detection_id", "defect_confidence", "severity", "recommended_action", "object_id", mode="before")
    @classmethod
    def _normalize_empty(cls, value: object) -> object:
        return blank_to_none(value)


class DefectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    object_id: int | None
    detection_id: int | None
    defect_type: str
    defect_confidence: float | None
    severity: str | None
    recommended_action: str | None
    bbox: list[float] | None
    source: str
    created_at: datetime
    updated_at: datetime
