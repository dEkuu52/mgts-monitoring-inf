"""Бизнес-логика пользователей и аутентификации."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.scalars(select(User).order_by(User.id))
    return list(result)


async def get_user(session: AsyncSession, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise AppError(404, "Пользователь не найден", f"Пользователь с id={user_id} не существует.")
    return user


async def find_by_login(session: AsyncSession, login: str) -> User | None:
    result = await session.scalars(
        select(User).where(or_(User.username == login, User.email == login))
    )
    return result.first()


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    await _ensure_unique(session, username=payload.username, email=payload.email)

    user = User(
        username=payload.username,
        email=str(payload.email),
        phone=payload.phone,
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user_id: int, payload: UserUpdate) -> User:
    user = await get_user(session, user_id)
    changes = payload.model_dump(exclude_unset=True)

    password = changes.pop("password", None)
    await _ensure_unique(
        session,
        username=changes.get("username"),
        email=str(changes["email"]) if changes.get("email") else None,
        exclude_id=user.id,
    )

    for field, value in changes.items():
        setattr(user, field, str(value) if field == "email" and value is not None else value)

    if password:
        user.password_hash = hash_password(password)

    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> None:
    user = await get_user(session, user_id)
    await session.delete(user)
    await session.commit()


async def authenticate(session: AsyncSession, login: str, password: str) -> User:
    user = await find_by_login(session, login)
    if user is None or not verify_password(password, user.password_hash):
        # Не раскрываем, что именно неверно: логин или пароль.
        raise AppError(401, "Неверные данные входа", "Проверьте имя пользователя и пароль.")
    return user


async def _ensure_unique(
    session: AsyncSession,
    *,
    username: str | None = None,
    email: str | None = None,
    exclude_id: int | None = None,
) -> None:
    conditions = []
    if username:
        conditions.append(User.username == username)
    if email:
        conditions.append(User.email == email)
    if not conditions:
        return

    statement = select(User).where(or_(*conditions))
    if exclude_id is not None:
        statement = statement.where(User.id != exclude_id)

    existing = (await session.scalars(statement)).first()
    if existing is None:
        return

    if username and existing.username == username:
        raise AppError(409, "Имя пользователя занято", f"Пользователь «{username}» уже существует.")
    raise AppError(409, "E-mail уже используется", f"Адрес {email} уже привязан к другому пользователю.")
