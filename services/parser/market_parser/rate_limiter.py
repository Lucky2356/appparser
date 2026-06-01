from __future__ import annotations

import os
import time
from threading import Lock


def parser_min_interval_seconds() -> float:
    return float(os.getenv("PARSER_MIN_INTERVAL_SECONDS", "0.05"))


class MarketplaceRateLimiter:
    def __init__(self) -> None:
        self._last_call: dict[str, float] = {}
        self._lock = Lock()

    def acquire(self, marketplace: str) -> float:
        min_interval = parser_min_interval_seconds()
        if min_interval <= 0:
            return 0

        with self._lock:
            now = time.monotonic()
            last_call = self._last_call.get(marketplace)
            wait_for = 0 if last_call is None else max(0, min_interval - (now - last_call))
            if wait_for:
                time.sleep(wait_for)
            self._last_call[marketplace] = time.monotonic()
            return wait_for


RATE_LIMITER = MarketplaceRateLimiter()
