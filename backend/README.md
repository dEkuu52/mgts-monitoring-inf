# Backend — API мониторинга инфраструктуры МГТС

Базовый REST API на **FastAPI** с асинхронной работой с **PostgreSQL**
(SQLAlchemy 2 + asyncpg). Реализует контракт, который уже использует фронтенд:
пользователи, статусы, объекты инфраструктуры и дефекты. Защищённые маршруты
поддерживают browser HTTP Basic через существующую базу пользователей и
сохраняют Bearer JWT для API-клиентов.

## Быстрый старт

### Через Docker (весь проект)

Из корня репозитория:

```bash
bash start-db.sh
```

Compose поднимет PostgreSQL, MinIO, API, ИИ-воркер и фронтенд. Swagger будет
доступен на <http://localhost:8000/docs>, API healthcheck — на
<http://localhost:8000/health>. Внутри docker-сети фронтенд обращается к API по
адресу `http://backend:8000` (передаётся через `API_PROXY_TARGET` в
`docker-compose.yml`).

Compose запускает одноразовый сервис `schema-init` с `postgres:15-alpine`
после готовности PostgreSQL и до запуска API или воркера. Он применяет
`backend/sql/schema.sql` через `psql` в одной транзакции. Демо-данные
автоматически не добавляются.

Воркер можно запустить/перезапустить отдельно:

```bash
docker compose up -d --build worker
docker compose logs -f worker
```

### Локально, без Docker

```bash
# 1. База данных (из корня проекта, один раз)
bash start-db.sh --db-only
#    либо: docker compose up -d db, затем применить схему через Compose (шаг 3)

# 2. Зависимости бэкенда
cd backend
py -3 -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# 3. Создание/обновление схемы БД (из корня проекта)
cd ..
docker compose run --rm schema-init

# 4. Демо-данные (необязательно, но удобно для проверки UI)
cd backend
python seed.py

# 5. Запуск API
uvicorn app.main:app --reload --port 3001

# 6. В другом терминале — ИИ-воркер (нужен ML-стек из requirements-worker.txt
#    и веса YOLO из папки cv; WEIGHTS_PATH при необходимости переопределить)
python worker.py
```

- Swagger: <http://127.0.0.1:3001/docs>
- Healthcheck: <http://127.0.0.1:3001/health>
- Порт `3001` совпадает с `devProxy` и `apiUrl` во фронтенде.

> Если фронтенд уже занял порт `3001`, освободите его или поменяйте
> `nitro.devProxy` в `frontend/nuxt.config.ts` и запустите API на другом порту.

## Подключение фронтенда

В `frontend/config.ts` выставить `useMocks: false`. Запросы пойдут на
`/api/...`, а Nuxt-прокси перенаправит их на `http://127.0.0.1:3001/api`.

Демо-пользователи после `python seed.py`:

| Логин | Пароль | Роль |
| --- | --- | --- |
| `admin` | `admin123` | admin |
| `operator` | `operator123` | operator |
| `engineer` | `engineer123` | engineer |

## Эндпоинты

| Метод | Путь | Описание |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Вход по `username`/`password`, возвращает Bearer JWT для API-клиентов |
| `GET` | `/api/auth/me` | Текущий пользователь по `Authorization: Basic ...` или `Authorization: Bearer <token>` |
| `GET`/`POST` | `/api/logout` | Заглушка для stateless Bearer API-клиентов; браузерный HTTP Basic кэш она не очищает |
| `GET`/`POST` | `/api/users`, `/api/users/{id}` | Пользователи |
| `PUT`/`DELETE` | `/api/users/{id}` | Обновление и удаление |
| `GET`/`POST` | `/api/statuses`, `/api/statuses/{id}` | Статусы |
| `PUT`/`DELETE` | `/api/statuses/{id}` | Обновление и удаление |
| `GET`/`POST` | `/api/infrastructure-objects`, `/{id}` | Объекты инфраструктуры |
| `PUT`/`DELETE` | `/api/infrastructure-objects/{id}` | Обновление и удаление |
| `POST` | `/api/infrastructure-objects/{id}/photo` | Загрузка или замена фото (multipart-поле `file`) |
| `GET` | `/api/infrastructure-objects/{id}/photo` | Фото объекта из MinIO |
| `DELETE` | `/api/infrastructure-objects/{id}/photo` | Удаление фото |
| `GET`/`POST` | `/api/defects`, `/api/defects/{id}` | Дефекты |
| `PUT`/`DELETE` | `/api/defects/{id}` | Обновление и удаление |
| `GET` | `/health` | Состояние сервиса и БД |

## Формат ответов

Успех (`2xx`):

```json
{ "success": true, "data": { "...": "..." } }
```

Ошибка (`4xx`/`5xx`):

```json
{
  "success": false,
  "error": {
    "code": 404,
    "title": "Объект не найден",
    "description": "Объект с id=42 не существует.",
    "message": "Объект с id=42 не существует."
  }
}
```

Конверт совместим с `frontend/services/useRequest.ts`, поэтому карточки и таблицы
работают без изменений.

## Структура

```text
backend/
├── app/
│   ├── main.py                 # create_app, lifespan, CORS, обработчики ошибок
│   ├── core/
│   │   ├── config.py           # настройки, читает корневой .env
│   │   ├── security.py         # bcrypt + JWT
│   │   ├── errors.py           # AppError и единый формат ошибок
│   │   ├── storage.py          # MinIO/S3: загрузка и выдача фото
│   │   ├── processing.py       # константы и утилиты очереди обработки
│   │   └── responses.py        # конверт успешного ответа
│   ├── db/
│   │   ├── base.py             # DeclarativeBase
│   │   └── session.py          # async engine и get_session
│   ├── models/                 # SQLAlchemy-модели таблиц
│   ├── schemas/                # Pydantic-схемы запросов/ответов
│   ├── services/               # бизнес-логика и запросы к БД (cv_logic.py — разбор детекций)
│   ├── worker.py               # ИИ-воркер: очередь -> YOLO -> дефекты/статусы
│   └── api/
│       ├── deps.py             # get_session, get_current_user, require_auth
│       ├── router.py           # сборка /api
│       └── routes/             # auth, users, statuses, objects, defects, health
├── sql/schema.sql              # идемпотентный источник схемы БД
├── seed.py                     # демо-данные
├── requirements.txt            # зависимости API
├── requirements-worker.txt     # API + PyTorch/Ultralytics/OpenCV для воркера
├── worker.Dockerfile           # образ воркера
└── main.py                     # запуск: uvicorn main:app
```

Слои повторяют подход из фронтенда и Go-проектов: транспорт (`api/routes`) →
сервисы (`services`) → модели (`models`), общие вещи — в `core`.
Зависимости передаются через `Depends`, ручной сборки графа нет.

## Схема БД

`backend/sql/schema.sql` — единственный источник схемы. Compose запускает
одноразовый `postgres:15-alpine` сервис `schema-init` с `psql -1` после
готовности базы и до API/воркера. При локальном запуске примените схему из
корня проекта:

```bash
docker compose run --rm schema-init
```

Инициализатор идемпотентно создаёт новую схему или дополняет существующие
legacy-таблицы и колонки без удаления данных; `alembic_version` и её данные,
если они остались в существующей базе, не затрагиваются. API, воркер и
`seed.py` схему не изменяют; `DB_BOOTSTRAP` больше не используется.
Демо-данные по-прежнему добавляются отдельно командой `python seed.py`.

Фото объектов хранятся в MinIO, а в `infrastructure_objects."imgUrl"` лежит
ключ файла вида `objects/{id}/{uuid}.jpg`. API отдаёт клиенту готовую ссылку
`/api/infrastructure-objects/{id}/photo`, поэтому менять схему БД не нужно.

## Обработка фото ИИ (воркер)

```
POST /api/infrastructure-objects/{id}/photo
        |  фото уходит в MinIO, объект получает processing_status = awaiting_processing
        v
worker.py  -- раз в WORKER_POLL_INTERVAL секунд берёт один объект из очереди
        |  processing_status = processing
        |  скачивает фото из MinIO (старые /uploads/raw/* — с диска)
        |  YOLO (веса из cv/ml/yolo-v/, по умолчанию 2-version.pt)
        |  -> дефекты в таблицу defects (source='cv'), статус ok/check_required/repair_required,
        |     тип и координаты из EXIF (если пусты), аннотированное фото в /uploads/processed/
        v  processing_status = done (или failed / снова awaiting_processing при ошибке)
```

Статусы в колонке `infrastructure_objects.processing_status`:
`awaiting_processing` (в ТЗ написано `awating_processing` — тоже понимается),
`processing`, `done`, `failed`. При замене/удалении фото счётчик попыток и
результаты сбрасываются. Дефекты воркера пересоздаются при повторной обработке,
ручные (`source='manual'`) не затрагиваются.

Воркер запускается отдельным процессом/сервисом (`docker compose up -d worker`),
не внутри API. Общий том `uploads_data` нужен, чтобы backend раздавал
`/uploads/processed/*`, а веса монтируются с хоста `./cv/ml/yolo-v:/weights:ro`.

## Переменные окружения

Обязательные берутся из `.env` в корне проекта: `DB_USER`, `DB_PASSWORD`,
`DB_NAME`, `DB_PORT`. Остальные — необязательные:

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `DB_HOST` | `localhost` | Хост PostgreSQL |
| `DB_ECHO` | `false` | Логировать SQL |
| `JWT_SECRET` | `dev-secret-change-me` | Секрет подписи токена (задать в проде) |
| `JWT_EXPIRES_MINUTES` | `720` | Время жизни токена |
| `AUTH_REQUIRED` | `false` | Требовать валидный Basic или Bearer заголовок для CRUD-эндпоинтов |
| `S3_ENDPOINT` | `http://localhost:9000` | Адрес MinIO/S3 (в Docker — `http://minio:9000`) |
| `S3_ACCESS_KEY` | `minioadmin` | Логин MinIO |
| `S3_SECRET_KEY` | `minioadmin` | Пароль MinIO |
| `S3_BUCKET` | `mgts-objects` | Bucket для фото объектов |
| `S3_REGION` | `us-east-1` | Регион S3 |
| `MAX_PHOTO_SIZE_MB` | `5` | Максимальный размер фото |
| `CORS_ORIGINS` | localhost:3000/3001 | Список origin через запятую |
| `WEIGHTS_PATH` | `cv/ml/yolo-v/2-version.pt` | Веса YOLO для воркера |
| `CV_MIN_CONFIDENCE` | `0.4` | Порог детекции |
| `CV_HIGH_CONFIDENCE` | `0.75` | Порог, ниже которого рекомендация «проверить» |
| `CV_IOU` / `CV_IMGSZ` | `0.5` / `640` | Параметры инференса |
| `WORKER_POLL_INTERVAL` | `3` | Период опроса очереди, сек |
| `WORKER_MAX_ATTEMPTS` | `3` | Попыток перед статусом `failed` |
| `WORKER_STALE_MINUTES` | `5` | Таймаут зависшей задачи, мин |
| `UPLOADS_DIR` | `<корень>/uploads` | Каталог `/uploads/raw` и `/uploads/processed` |

Локальный preview оставляет `AUTH_REQUIRED=false`, чтобы работать без отдельного
gateway. В hosted Compose `AUTH_REQUIRED=true`: browser HTTP Basic проверяется
через существующий `user_service.authenticate`, а Bearer JWT остаётся доступен
для API-клиентов. Форма входа и frontend JWT-cookie не используются.

## Дальше по плану

- `GET /frames/{id}/image` для просмотра кадров;
- фильтры и пагинация (`severity`, `action`, `limit`, `offset`);
- экспорт `GET /api/defects/export?format=csv`;
- загрузка `imgUrl` в файловое хранилище.
