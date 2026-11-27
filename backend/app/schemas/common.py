"""Общие схемы и хелперы валидации."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """Конверт ответа, который ожидает фронтенд."""

    success: bool = True
    data: T


def blank_to_none(value: Any) -> Any:
    """Пустая строка из HTML-формы трактуется как отсутствие значения."""
    if isinstance(value, str) and not value.strip():
        return None
    return value
