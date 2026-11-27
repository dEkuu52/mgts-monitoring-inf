from fastapi import APIRouter

from app.api.deps import SessionDep, CurrentUser
from app.core.errors import AppError
from app.core.responses import ok
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import Envelope
from app.schemas.user import UserRead
from app.services import user_service

router = APIRouter(tags=["Авторизация"])


@router.post("/auth/login", response_model=Envelope[LoginResponse])
async def login(payload: LoginRequest, session: SessionDep):
    user = await user_service.authenticate(session, payload.username, payload.password)
    token = create_access_token(
        subject=str(user.id),
        extra={"username": user.username, "role": user.role},
    )
    return ok(LoginResponse(token=token, user=UserRead.model_validate(user)))


@router.get("/auth/me", response_model=Envelope[UserRead])
async def me(user: CurrentUser):
    if user is None:
        raise AppError(401, "Требуется авторизация", "Передайте действующий заголовок Authorization.")
    return ok(user)


@router.post("/logout", response_model=Envelope[bool], operation_id="logout")
async def logout():
    # Токен stateless: клиент просто удаляет его у себя.
    return ok(True)


@router.get("/logout", response_model=Envelope[bool], include_in_schema=False)
async def logout_get():
    # Фронтенд вызывает выход через GET (frontend/layouts/admin.vue).
    return ok(True)
