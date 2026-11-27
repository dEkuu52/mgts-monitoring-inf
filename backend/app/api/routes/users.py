from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_auth
from app.core.responses import ok
from app.schemas.common import Envelope
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(
    prefix="/users",
    tags=["Пользователи"],
    dependencies=[Depends(require_auth)],
)


@router.get("", response_model=Envelope[list[UserRead]])
async def list_users(session: SessionDep):
    return ok(await user_service.list_users(session))


@router.get("/{user_id}", response_model=Envelope[UserRead])
async def get_user(user_id: int, session: SessionDep):
    return ok(await user_service.get_user(session, user_id))


@router.post("", response_model=Envelope[UserRead], status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, session: SessionDep):
    return ok(await user_service.create_user(session, payload))


@router.put("/{user_id}", response_model=Envelope[UserRead])
async def update_user(user_id: int, payload: UserUpdate, session: SessionDep):
    return ok(await user_service.update_user(session, user_id, payload))


@router.delete("/{user_id}", response_model=Envelope[bool])
async def delete_user(user_id: int, session: SessionDep):
    await user_service.delete_user(session, user_id)
    return ok(True)
