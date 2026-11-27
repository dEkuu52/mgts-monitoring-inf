# Образ ИИ-воркера. Собирается из корня проекта:
#   docker compose build worker
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# opencv-python (зависимость ultralytics) нужен libgl1 на slim-образе.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
COPY backend/requirements-worker.txt ./requirements-worker.txt
# Только CPU-сборки torch/torchvision: обычный PyPI тянет гигабайты CUDA-библиотек.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.15.0 torchvision==0.29.2
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY backend/app ./app
COPY backend/worker.py backend/main.py backend/seed.py ./

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app
USER appuser

# Веса монтируются в /weights (см. docker-compose.yml), фото — общий том /app/uploads.
CMD ["python", "worker.py"]
