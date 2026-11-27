"""Точка входа для запуска `uvicorn main:app --reload` из папки backend."""

from app.main import app

__all__ = ["app"]
