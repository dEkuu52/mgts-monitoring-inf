from pydantic import BaseModel, ConfigDict, Field


class StatusBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: str = Field(min_length=1, max_length=100)
    description: str | None = None


class StatusCreate(StatusBase):
    pass


class StatusUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class StatusRead(StatusBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
