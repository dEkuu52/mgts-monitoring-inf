from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import blank_to_none


class UserBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    role: str = Field(default="user", max_length=50)

    @field_validator("phone", mode="before")
    @classmethod
    def _normalize_phone(cls, value: object) -> object:
        return blank_to_none(value)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str | None = Field(default=None, min_length=3, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    role: str | None = Field(default=None, max_length=50)
    password: str | None = Field(default=None, min_length=6, max_length=128)

    @field_validator("phone", "role", mode="before")
    @classmethod
    def _normalize_optional_strings(cls, value: object) -> object:
        return blank_to_none(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    phone: str | None
    role: str
    created_at: datetime
    updated_at: datetime
