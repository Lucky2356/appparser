# Appsparcer

Web app for finding value offers across marketplaces. The default launch mode uses real Ozon and Wildberries source adapters. Mock and hybrid modes are available only when explicitly selected for tests or demos.

## Stack

- Frontend: React, TypeScript, Vite, TailwindCSS
- Backend: FastAPI, SQLAlchemy, JWT auth
- Background jobs: Celery, Redis
- Database: PostgreSQL
- Parser layer: marketplace adapters with a shared normalized offer model

## Quick Local Run

This starts the API and web app locally without Docker. It uses SQLite in `.runtime/` and real parser data by default.

```powershell
.\start.cmd
```

Open:

- Web: http://localhost:5173
- API docs: http://localhost:8000/docs

Run a local demo with deterministic mock data:

```powershell
.\start.cmd -ParserMode mock
```

## Run with Docker

```powershell
.\start-docker.cmd
```

Open:

- Web: http://localhost:3000
- API docs: http://localhost:8001/docs

Run Docker in background:

```powershell
.\start-docker.cmd -Detached
```

Run Docker with deterministic mock data:

```powershell
.\start-docker.cmd -ParserMode mock
```

The Docker launcher pulls base images sequentially with retries to reduce transient Docker Hub TLS timeouts. If base images are already cached locally and Docker Hub is temporarily unavailable, run:

```powershell
.\start-docker.cmd -SkipBasePull
```

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
- Real Ozon and Wildberries adapters in `PARSER_MODE=real`
- Browser-backed live fallback for Wildberries rate-limit cases
- Optional `hybrid` mode for development demos with mock fallback
- Runtime parser logs showing whether data came from `mock`, `live`, `fallback`, or `failed` sources
- PWA manifest and service worker
- Alembic migrations
- Backend smoke tests
- GitHub Actions CI workflow
- Docker-ready local environment

## Development

Parser modes:

- `PARSER_MODE=real`: live Ozon/Wildberries collection only. If live sources block or return no usable product data, the search fails with source logs instead of showing mock products.
- `PARSER_MODE=hybrid`: tries live Ozon/Wildberries collection first, then falls back to deterministic demo data if a source rate-limits, blocks, or returns an unexpected page.
- `PARSER_MODE=mock`: deterministic local data for tests and development.

Live collection uses `PARSER_HTTP_TIMEOUT_SECONDS`, `PARSER_HTTP_PROXY`, `PARSER_USER_AGENT`, `PARSER_BROWSER_FALLBACK`, `OZON_COOKIES`, `OZON_COOKIES_FILE`, `OZON_STORAGE_STATE_FILE`, `WILDBERRIES_COOKIES`, `WILDBERRIES_COOKIES_FILE`, `WILDBERRIES_STORAGE_STATE_FILE`, and `WILDBERRIES_DEST` from the environment. Wildberries can fall back to a Chromium-backed request when regular HTTP is rate-limited. Ozon can still return an anti-bot 403 without valid session cookies/storage state/proxy access, so the app keeps source status visible in result logs and never treats mock data as real results.

Product cards load remote marketplace images through the API image proxy (`/images/proxy`). The proxy is restricted to known Ozon/Wildberries image hosts and keeps the original image URL stored in the database.

For Ozon, the most stable local setup is a saved browser session:

```powershell
.\scripts\save-ozon-session.ps1
```

Then set `OZON_STORAGE_STATE_FILE=/app/.runtime/ozon-storage-state.json` in `.env` before starting Docker. The compose file mounts `.runtime` into the API and worker containers.

You can verify Ozon access without starting the full stack:

```powershell
.\scripts\test-ozon-access.ps1 -Query iphone
```

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
