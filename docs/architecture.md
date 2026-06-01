# Architecture

## Runtime flow

```txt
React Web -> FastAPI -> PostgreSQL
                 |
                 v
              Redis Queue -> Celery Worker -> Parser Adapters -> Scoring -> PostgreSQL
```

The frontend never talks to marketplaces directly. It creates a search task through the API, polls status, and renders stored normalized offers.

## Boundaries

- `apps/web`: user interface, auth state, search workflow, history, favorites, tracked products.
- `apps/api`: REST API, persistence, authorization, task scheduling.
- `services/parser`: marketplace adapter contract, mock Ozon/Wildberries adapters, normalization, score calculation.

## Parser strategy

The MVP intentionally uses mock adapters. The adapter interface already models the real boundary:

```py
class MarketplaceAdapter:
    marketplace_name: str

    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        ...
```

Real adapters should add legal source checks, robots.txt awareness where applicable, structured logging, and defensive parsing. A broken adapter must return a log entry or raise an adapter-scoped error without failing the whole search.

The current parser layer already includes in-process TTL caching and per-marketplace rate limiting. In production, this can be swapped to Redis-backed cache/limits without changing adapter contracts.

`PARSER_MODE=mock` is the stable default. `PARSER_MODE=hybrid` enables best-effort HTTP collection where an adapter supports it and falls back to mock data if the source is unavailable. `PARSER_MODE=real` disables fallback for adapters that implement live collection.

## Scoring

Offers are ranked by weighted factors:

- price compared to average price
- product rating
- review count
- discount percent
- seller rating
- availability

Weights live in `services/parser/market_parser/scoring.py` and are intentionally easy to tune.

## Database lifecycle

Alembic migrations live in `apps/api/migrations`. Docker runs `alembic upgrade head` before starting API and worker containers. `AUTO_CREATE_TABLES=true` remains available for quick local SQLite development only.

## Notifications

Tracked product refreshes write price history. When a price drops or reaches a target price, the backend creates an in-app notification. Docker includes a Celery beat service that schedules refreshes hourly.

Telegram delivery is optional. Set `TELEGRAM_BOT_TOKEN`, then users can add their chat ID in Settings. The app keeps in-app notifications even when Telegram delivery is disabled or fails.

Tracked products store marketplace `external_id` when they are created from search results. Refreshes first try to match the same normalized offer by `external_id`, then by URL, then fall back to the best current search result.
