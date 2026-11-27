from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserRead
