from market_parser.cache import OFFER_CACHE, build_cache_key
from market_parser.adapters.registry import get_adapters
from market_parser.adapters.runtime import AdapterRuntime
from market_parser.models import MarketplaceOffer, ParserLogEntry, ParserResult, SearchParams
from market_parser.rate_limiter import RATE_LIMITER


def collect_offers(params: SearchParams) -> ParserResult:
    adapters = get_adapters()
    offers: list[MarketplaceOffer] = []
    logs: list[ParserLogEntry] = []
    seen: set[tuple[str, str]] = set()

    for marketplace in params.marketplaces:
        key = marketplace.lower().strip()
        adapter = adapters.get(key)
        if not adapter:
            logs.append(ParserLogEntry(marketplace=key, level="warning", message="Marketplace adapter is not enabled"))
            continue

        try:
            cache_key = build_cache_key(key, params)
            adapter_offers = OFFER_CACHE.get(cache_key)
            if adapter_offers is None:
                waited = RATE_LIMITER.acquire(key)
                adapter_offers = adapter.search_products(params)
                OFFER_CACHE.set(cache_key, adapter_offers)
                if waited:
                    logs.append(
                        ParserLogEntry(
                            marketplace=key,
                            level="info",
                            message=f"Applied rate limit delay {waited:.2f}s",
                        )
                    )
                runtime = getattr(adapter, "runtime", AdapterRuntime(source="unknown"))
                logs.append(
                    ParserLogEntry(
                        marketplace=key,
                        level=_runtime_log_level(runtime.source),
                        message=_runtime_message(runtime),
                    )
                )
            else:
                logs.append(ParserLogEntry(marketplace=key, level="info", message="Used cached parser results"))

            for offer in adapter_offers:
                identity = (offer.marketplace, offer.external_id)
                if identity in seen:
                    continue
                seen.add(identity)
                offers.append(offer)
            logs.append(
                ParserLogEntry(
                    marketplace=key,
                    level="info",
                    message=f"Collected {len(adapter_offers)} normalized offers",
                )
            )
        except Exception as exc:  # noqa: BLE001
            runtime = getattr(adapter, "runtime", None)
            if isinstance(runtime, AdapterRuntime) and runtime.source in {"failed", "fallback"}:
                logs.append(
                    ParserLogEntry(
                        marketplace=key,
                        level=_runtime_log_level(runtime.source),
                        message=_runtime_message(runtime),
                    )
                )
            logs.append(ParserLogEntry(marketplace=key, level="error", message=str(exc)))

    return ParserResult(offers=offers, logs=logs)


def _runtime_log_level(source: str) -> str:
    if source == "failed":
        return "error"
    if source == "fallback":
        return "warning"
    return "info"


def _runtime_message(runtime: AdapterRuntime) -> str:
    return f"Adapter source: {runtime.source}" + (f" ({runtime.detail})" if runtime.detail else "")
