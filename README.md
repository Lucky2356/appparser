# Appsparcer

MVP web app for finding value offers across marketplaces. The first version uses mock Ozon and Wildberries adapters so the product flow, API, database, queue, scoring, history, and favorites work before real parsers are connected.

## Stack

- Frontend: React, TypeScript, Vite, TailwindCSS
- Backend: FastAPI, SQLAlchemy, JWT auth
- Background jobs: Celery, Redis
- Database: PostgreSQL
- Parser layer: marketplace adapters with a shared normalized offer model

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs

## MVP features

- Register, login, JWT session
- Marketplace selection: Ozon and Wildberries
- Search by product name
- Filters: rating, reviews, min/max price
- Async search task through Celery
- Normalized offers
- Top-20 result ranking with score explanations
- Search history
- CSV export for search results
- Favorites
- Tracked products screen
- Price history for tracked products
- Product identity matching for tracked price refreshes
- In-app notifications for price drops and target price hits
- Optional Telegram notifications through Bot API
- Hourly Celery beat task for tracked product refresh
- Parser cache and per-marketplace rate limiting
- Optional Wildberries HTTP adapter in `PARSER_MODE=hybrid`
- PWA manifest and service worker
- Alembic migrations
- Backend smoke tests
- GitHub Actions CI workflow
- Docker-ready local environment

## Development

Backend:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH="..\..;..\..\services\parser"
uvicorn app.main:app --reload
```

Migrations:

```bash
cd apps/api
$env:PYTHONPATH="D:\appsparcer\apps\api;D:\appsparcer\services\parser"
alembic -c alembic.ini upgrade head
```

Tests:

```bash
cd apps/api
$env:PYTHONPATH="D:\appsparcer\apps\api;D:\appsparcer\services\parser"
python -m pytest -q
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

## Architecture

```txt
apps/web        React client
apps/api        FastAPI API and Celery tasks
services/parser Marketplace adapters and scoring
infra           Reserved for deployment/runtime assets
docs            Architecture and API notes
```

The parser contract is adapter-based. Real marketplace integrations should replace the mock adapters gradually while keeping the normalized `MarketplaceOffer` shape intact.

Additional notes:

- `docs/architecture.md`
- `docs/api.md`
