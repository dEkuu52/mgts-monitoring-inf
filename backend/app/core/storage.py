"""Работа с S3-совместимым хранилищем (MinIO).

Файлы хранятся в приватном bucket. Наружу они отдаются только через API,
поэтому клиенту не нужны ни доступы к MinIO, ни presigned-ссылки.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)


@lru_cache
def _client():
    """Ленивый клиент boto3: создаётся один раз на процесс."""
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=BotoConfig(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=5,
            read_timeout=30,
            retries={"max_attempts": 2},
        ),
    )


def _ensure_bucket_sync() -> None:
    client = _client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        try:
            client.create_bucket(Bucket=settings.s3_bucket)
        except ClientError as create_exc:
            create_code = str(create_exc.response.get("Error", {}).get("Code", ""))
            if create_code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                raise
        logger.info("Создан bucket %s", settings.s3_bucket)


async def ensure_bucket(attempts: int = 5, delay: float = 1.0) -> None:
    """Создаёт bucket при старте. Без MinIO API всё равно поднимается."""
    for attempt in range(1, attempts + 1):
        try:
            await run_in_threadpool(_ensure_bucket_sync)
            return
        except (BotoCoreError, ClientError) as exc:
            if attempt == attempts:
                logger.warning(
                    "MinIO недоступен, bucket %s не создан: %s",
                    settings.s3_bucket,
                    exc,
                )
                return
            logger.info(
                "MinIO пока недоступен (попытка %d/%d), повтор через %.1f с",
                attempt,
                attempts,
                delay,
            )
            await asyncio.sleep(delay)


def _put_object_sync(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


async def put_object(key: str, data: bytes, content_type: str) -> None:
    try:
        await run_in_threadpool(_put_object_sync, key, data, content_type)
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Не удалось сохранить %s в MinIO: %s", key, exc)
        raise AppError(
            503,
            "Хранилище недоступно",
            "Не удалось сохранить фото. Попробуйте повторить попытку позже.",
        ) from exc


def _get_object_sync(key: str) -> tuple[bytes, str]:
    response = _client().get_object(Bucket=settings.s3_bucket, Key=key)
    body = response["Body"]
    try:
        data = body.read()
    finally:
        body.close()
    return data, response.get("ContentType") or "application/octet-stream"


async def get_object(key: str) -> tuple[bytes, str]:
    try:
        return await run_in_threadpool(_get_object_sync, key)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise AppError(404, "Фото не найдено", "Файл отсутствует в хранилище.") from exc
        logger.warning("Не удалось прочитать %s из MinIO: %s", key, exc)
        raise AppError(
            503,
            "Хранилище недоступно",
            "Не удалось получить фото. Попробуйте повторить попытку позже.",
        ) from exc
    except BotoCoreError as exc:
        logger.warning("Не удалось прочитать %s из MinIO: %s", key, exc)
        raise AppError(
            503,
            "Хранилище недоступно",
            "Не удалось получить фото. Попробуйте повторить попытку позже.",
        ) from exc


def _delete_object_sync(key: str) -> None:
    _client().delete_object(Bucket=settings.s3_bucket, Key=key)


async def delete_object(key: str) -> None:
    """Удаляет файл. Ошибка только логируется: БД уже обновлена."""
    try:
        await run_in_threadpool(_delete_object_sync, key)
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Не удалось удалить %s из MinIO: %s", key, exc)
