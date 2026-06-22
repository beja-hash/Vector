# Vector

Vector — внутренний инструмент ConnectUp для поиска и квалификации компаний под ICP клиента. Это не лендинг и не публичный SaaS: сейчас приложение предназначено для команды, чтобы быстрее собирать базы компаний под клиентские проекты.

## Что уже есть

- React + TypeScript + Vite frontend с dashboard, проектами, wizard создания поиска и страницей результатов.
- FastAPI backend с REST API, SQLAlchemy-моделями, Pydantic-схемами и PostgreSQL.
- Mock provider, который генерирует реалистичные компании по фильтрам ICP.
- Сохранение проектов, поисков и результатов в базе.
- CSV export результатов поиска.
- Базовая Alembic-структура для будущих миграций.

Vector сейчас работает на mock provider.
Реальные источники данных будут подключаться через интерфейс `CompanyProvider`.

## Запуск через Docker

```bash
docker compose up --build
```

После запуска:

- frontend: http://localhost:5173
- backend: http://localhost:8000
- healthcheck: http://localhost:8000/api/health
- PostgreSQL: localhost:5432, база `vector`, пользователь `postgres`, пароль `postgres`

Если локальные порты заняты, можно переопределить published ports:

```bash
BACKEND_PORT=8010 FRONTEND_PORT=5174 POSTGRES_PORT=5545 VITE_API_BASE_URL=http://localhost:8010 docker compose up --build
```

## Backend отдельно

Нужен запущенный PostgreSQL и переменная `DATABASE_URL`.

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

По умолчанию backend ожидает:

```text
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/vector
```

## Frontend отдельно

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend обращается к backend через:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## API

- `GET /api/health`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `GET /api/searches`
- `POST /api/searches`
- `GET /api/searches/{search_id}`
- `GET /api/searches/{search_id}/results`
- `GET /api/searches/{search_id}/export.csv`

`POST /api/searches` создаёт или использует проект, создаёт поиск, запускает `MockProvider`, сохраняет компании и возвращает созданный поиск.

## Где подключать реальные источники

Интерфейс провайдера находится в:

```text
backend/app/services/company_providers/base.py
```

Текущая реализация:

```text
backend/app/services/company_providers/mock_provider.py
```

Следующий реальный источник нужно добавлять отдельным классом, реализующим `CompanyProvider.search_companies`. Оркестрация запуска поиска находится в:

```text
backend/app/services/search_runner.py
```

Так можно подключить Rusprofile, HH, 2ГИС, Контур, DaData, ФНС или другие источники позже, не переписывая API и frontend.
