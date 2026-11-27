"""Точка сборки приложения."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app import __version__
from app.api.router import api_router
from app.api.routes import health
from app.core import storage
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.session import dispose_engine

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await storage.ensure_bucket()
    logger.info("API готово: http://127.0.0.1:3001%s", settings.api_prefix)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uploads_dir = settings.uploads_path
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(health.router)

    return app


app = create_app()
