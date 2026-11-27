"""Общие зависимости FastAPI."""

from __future__ import annotations

import base64
import binascii
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.security import decode_token
from app.db.session import get_session
from app.models.user import User
from app.services import user_service

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(request: Request, session: SessionDep) -> User | None:
    """Пользователь из Basic credentials или существующего Bearer JWT."""
    header = request.headers.get("Authorization", "")
    scheme, _, raw_token = header.partition(" ")
    token = raw_token.strip()

    if scheme.lower() == "basic":
        if not token:
            return None

        try:
            credentials = base64.b64decode(token, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeError, ValueError):
            return None

        login, separator, password = credentials.partition(":")
        if not separator or not login or "\x00" in credentials:
            return None

        try:
            return await user_service.authenticate(session, login, password)
        except AppError as error:
            if error.status_code == 401:
                return None
            raise

    if scheme.lower() != "bearer" or not token:
        return None

    payload = decode_token(token, raise_on_error=False)
    if payload is None:
        return None

    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        return None

    return await session.get(User, user_id)


CurrentUser = Annotated[User | None, Depends(get_current_user)]


async def require_auth(user: CurrentUser) -> User | None:
    """Проверяет учетные данные, если защита включена через `AUTH_REQUIRED=true`."""
    if settings.auth_required and user is None:
        raise AppError(401, "Требуется авторизация", "Войдите в систему, чтобы продолжить.")
    return user


AuthGuard = Annotated[User | None, Depends(require_auth)]
