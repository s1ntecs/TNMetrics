# Metrics API + Admin

Реализация тестового задания: REST API для метрик и записей метрик с JWT-авторизацией, кэшированием на Redis, фоновой задачей Celery Beat и админ-панелью.

## Цель проекта

Сервис позволяет:

- создавать пользовательские метрики (`Metric`);
- добавлять к метрикам значения во времени (`MetricRecord`);
- связывать записи с тегами (`Tag`);
- управлять пользователями и справочником тегов через админ-панель.

Метрики и записи изолированы по пользователю, теги общие.

## Соответствие ТЗ

- Запуск через `docker-compose`: реализовано (`docker-compose.yml`).
- PostgreSQL как основная БД: реализовано.
- Redis как кэш и брокер/бэкенд Celery: реализовано.
- Простая JWT-авторизация: реализовано через `POST /api/token/` и `Bearer` токен.
- Автосоздание суперпользователя + добавление пользователей через админ-панель: реализовано.
- Кэширование списка записей метрики + инвалидация при создании новой записи: реализовано.
- Celery Beat задача раз в 2 минуты с фейк-отчетом: реализовано (`reports/fake_report.txt`).
- Админ-панель для `Metric`, `MetricRecord`, `Tag`: реализовано (SQLAdmin).
- Эндпоинт создания записи метрики покрыт тестами: реализовано (`tests/test_create_record.py`).
- Настройка линтеров и типизации: реализовано (`ruff`, `mypy` в `pyproject.toml`).

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (async) + Alembic
- PostgreSQL
- Redis
- Celery Worker + Celery Beat
- SQLAdmin
- JWT (`python-jose`) + `passlib`
- Pytest + Ruff + MyPy

## Модели данных

- `Metric`: `id`, `user_id`, `name`, `description`, `created_at`.
- `MetricRecord`: `id`, `metric_id`, `timestamp`, `value`, `created_at`.
- `Tag`: `id`, `name`, `created_at`.
- Связь `MetricRecord <-> Tag`: many-to-many (`metric_record_tags`).

## Быстрый старт

### 1. Подготовка окружения

Требуется установленный Docker и Docker Compose.

```bash
cp .env.example .env
```

При необходимости измените секрет и пароли в `.env`.

Для PowerShell:

```powershell
Copy-Item .env.example .env
```

Ключевые переменные:

- `SECRET_KEY` - секрет для подписи JWT и сессий админки.
- `POSTGRES_*` - параметры подключения к PostgreSQL.
- `REDIS_*` - параметры Redis для кэша и Celery.
- `SUPERUSER_EMAIL`, `SUPERUSER_PASSWORD` - учетка суперпользователя админки.
- `CACHE_TTL_SECONDS` - TTL кэша списка записей.
- `REPORTS_DIR` - директория для фейк-отчета.

### 2. Запуск всех сервисов

```bash
docker compose up --build
```

Или через Makefile:

```bash
make up
```

Сервисы:

- `api` на `8000`
- `admin` на `8001`
- `db` (PostgreSQL)
- `redis`
- `celery_worker`
- `celery_beat`

Миграции (`alembic upgrade head`) выполняются при старте `api` и `admin`.

### 3. Полезные URL

- Swagger API: `http://localhost:8000/docs`
- Admin UI: `http://localhost:8001/admin`
- Health API: `http://localhost:8000/health`
- Health Admin: `http://localhost:8001/health`

## Первая настройка и работа

### 1. Вход в админку

- Откройте `http://localhost:8001/admin`.
- Логин: email суперпользователя из `.env` (`SUPERUSER_EMAIL`).
- Пароль: `SUPERUSER_PASSWORD`.

Суперпользователь создается автоматически при старте admin-приложения, если его нет в БД.

### 2. Добавление данных через админку

- Создайте обычных пользователей в разделе `Users`.
- Создайте теги в разделе `Tags`.

### 3. Получение JWT токена

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

Ответ содержит `access_token`.

### 4. Использование токена

Во все защищенные методы передавайте заголовок:

```bash
Authorization: Bearer <access_token>
```

## Эндпоинты из ТЗ

- `POST /api/token/` - получить JWT токен.
- `POST /api/metrics/` - создать метрику (требуется авторизация).
- `GET /api/metrics/` - список метрик пользователя (требуется авторизация).
- `GET /api/tags/` - список тегов (требуется авторизация).
- `GET /api/metrics/{metric_id}/records/` - список записей метрики (требуется авторизация, кэшируется).
- `GET /api/metrics/{metric_id}/records/{record_id}` - получить одну запись метрики (требуется авторизация).
- `POST /api/metrics/{metric_id}/records/` - создать запись метрики (требуется авторизация, покрыто тестами).

## Кэширование списка записей

Для `GET /api/metrics/{metric_id}/records/` используется Redis:

- ключ версии: `records_ver:{user_id}:{metric_id}`
- ключ данных: `records:{user_id}:{metric_id}:v{ver}:limit{L}:offset{O}`

При создании записи (`POST /api/metrics/{metric_id}/records/`) версия увеличивается (`INCR`), старые ключи становятся неактуальными.

## Celery Beat: фейк-отчет

- Период запуска: каждые 2 минуты.
- Задача: `src.infrastructure.celery.tasks.reporting.generate_fake_report`.
- Файл отчета: `reports/fake_report.txt`.

Содержимое файла:

- `total_metrics=<число>`
- `total_records=<число>`
- `updated_at=<UTC timestamp>`

Проверка на хосте:

```bash
cat reports/fake_report.txt
```

Для PowerShell:

```powershell
Get-Content reports/fake_report.txt
```

## Проверка качества кода

Через `make`:

```bash
make lint
make typecheck
make test
```

Если локально не установлены `ruff`, `mypy` или `pytest`, `Makefile` автоматически запускает эти проверки внутри контейнера `api`.

Или напрямую:

```bash
ruff check .
ruff format --check .
mypy src
pytest -q
```

## Остановка проекта

```bash
docker compose down
```

Или:

```bash
make down
```
