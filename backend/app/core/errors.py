"""Единый формат ошибок API.

Фронтенд (`frontend/services/useRequest.ts`) ожидает на ошибку объект вида:

    {
        "code": 404,
        "title": "Запись не найдена",
        "description": "...",
        "message": "..."
    }

Поэтому приложение всегда отвечает конвертом:
    успех  -> {"success": true,  "data": ...}
    ошибка -> {"success": false, "error": {"code", "title", "description", "message"}}
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Ошибка уровня приложения, которую можно безопасно показать клиенту."""

    def __init__(
        self,
        status_code: int = 400,
        title: str = "Ошибка",
        description: str = "",
        *,
        code: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code or status_code
        self.title = title
        self.description = description
        self.message = description or title
        super().__init__(self.message)


def error_content(code: int, title: str, description: str, message: str | None = None) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "title": title,
            "description": description,
            "message": message or description,
        },
    }


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_content(exc.code, exc.title, exc.description, exc.message),
    )


FIELD_LABELS = {
    "username": "Имя пользователя",
    "email": "E-mail",
    "password": "Пароль",
    "phone": "Телефон",
    "role": "Роль",
    "type": "Тип",
    "description": "Описание",
    "external_id": "Внешний идентификатор",
    "place": "Место",
    "lat": "Широта",
    "lon": "Долгота",
    "status_id": "Статус",
    "img_url": "Ссылка на изображение",
    "object_id": "Объект",
    "detection_id": "ID наблюдения",
    "defect_type": "Признак дефекта",
    "defect_confidence": "Уверенность",
    "severity": "Критичность",
    "recommended_action": "Рекомендованное действие",
}

MESSAGE_BY_TYPE = {
    "missing": "обязательное поле",
    "string_too_short": "слишком короткое значение",
    "string_too_long": "слишком длинное значение",
    "string_type": "ожидается строка",
    "int_parsing": "ожидается целое число",
    "int_type": "ожидается целое число",
    "float_parsing": "ожидается число",
    "float_type": "ожидается число",
    "greater_than_equal": "значение слишком маленькое",
    "less_than_equal": "значение слишком большое",
    "bool_parsing": "ожидается true или false",
    "value_error": "неверное значение",
}


def _validation_details(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", ()) if part != "body"]
        field = location[-1] if location else ""
        label = FIELD_LABELS.get(field, field)

        if field == "email":
            message = "неверный адрес электронной почты"
        else:
            message = MESSAGE_BY_TYPE.get(error.get("type", ""), "неверное значение")

        parts.append(f"{label}: {message}" if label else message)

    return "; ".join(parts) or "Проверьте корректность отправленных данных"


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_content(422, "Неверные данные", _validation_details(exc)),
    )


async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Нарушение целостности данных: %s", exc.orig)
    return JSONResponse(
        status_code=409,
        content=error_content(
            409,
            "Конфликт данных",
            "Запись нарушает ограничения базы данных: возможно, такое значение уже существует.",
        ),
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Необработанная ошибка", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=error_content(500, "Внутренняя ошибка", "Попробуйте повторить попытку позже."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
