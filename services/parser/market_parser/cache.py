from __future__ import annotations

import copy
import json
import os
import time
from dataclasses import asdict
from threading import Lock

from market_parser.models import MarketplaceOffer, SearchParams


def parser_cache_ttl_seconds() -> int:
    return int(os.getenv("PARSER_CACHE_TTL_SECONDS", "300"))


def build_cache_key(marketplace: str, params: SearchParams) -> str:
    payload = {
        "marketplace": marketplace,
        "query": params.query.strip().lower(),
        "filters": asdict(params.filters),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


class OfferCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, list[MarketplaceOffer]]] = {}
        self._lock = Lock()

    def get(self, key: str) -> list[MarketplaceOffer] | None:
        now = time.monotonic()
        ttl = parser_cache_ttl_seconds()
        with self._lock:
            item = self._items.get(key)
            if not item:
                return None
            created_at, offers = item
            if now - created_at > ttl:
                self._items.pop(key, None)
                return None
            return copy.deepcopy(offers)

    def set(self, key: str, offers: list[MarketplaceOffer]) -> None:
        with self._lock:
            self._items[key] = (time.monotonic(), copy.deepcopy(offers))

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


OFFER_CACHE = OfferCache()
