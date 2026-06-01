from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx
from market_parser.adapters.base import MarketplaceAdapter
from market_parser.adapters.mock_base import BaseMockMarketplaceAdapter
from market_parser.adapters.runtime import AdapterRuntime, RuntimeAwareAdapter
from market_parser.errors import AdapterUnavailableError
from market_parser.models import MarketplaceOffer, SearchParams


class WildberriesMockAdapter(BaseMockMarketplaceAdapter):
    marketplace_name = "wildberries"
    display_name = "Wildberries"
    brand_color = "fce7f3"
    price_multiplier = 0.97

    def _product_url(self, external_id: str, query: str) -> str:
        return f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote_plus(query)}&mock_id={external_id}"


class WildberriesHttpAdapter(MarketplaceAdapter):
    marketplace_name = "wildberries"

    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        errors: list[str] = []
        timeout = float(os.getenv("PARSER_HTTP_TIMEOUT_SECONDS", "8"))

        with httpx.Client(headers=_wildberries_headers(), follow_redirects=True, timeout=timeout) as client:
            for version, url in _wildberries_search_urls(params.query):
                try:
                    response = client.get(url)
                    if response.status_code == 429:
                        errors.append(f"{version}: rate limited")
                        continue
                    response.raise_for_status()
                    payload = response.json()
                except httpx.HTTPStatusError as exc:
                    errors.append(f"{version}: HTTP {exc.response.status_code}")
                    continue
                except (httpx.HTTPError, ValueError) as exc:
                    errors.append(f"{version}: {exc.__class__.__name__}")
                    continue

                products = payload.get("data", {}).get("products", [])
                if not isinstance(products, list):
                    errors.append(f"{version}: unexpected payload")
                    continue

                offers = [self._normalize_product(product) for product in products[:40]]
                offers = [offer for offer in offers if offer is not None]
                filtered = self._apply_filters(offers, params)
                if filtered:
                    return filtered
                errors.append(f"{version}: no matching offers")

        detail = "; ".join(errors[:5]) if errors else "no Wildberries endpoints tried"
        raise AdapterUnavailableError(self.marketplace_name, f"Wildberries endpoint unavailable: {detail}")

    def _normalize_product(self, product: dict) -> MarketplaceOffer | None:
        product_id = product.get("id")
        title = product.get("name")
        price = _extract_price(product)
        if not product_id or not title or not price:
            return None

        old_price = _extract_old_price(product)
        discount = None
        if old_price and old_price > price:
            discount = round((old_price - price) / old_price * 100)

        return MarketplaceOffer(
            external_id=f"wildberries-{product_id}",
            marketplace=self.marketplace_name,
            title=str(title),
            price=float(price),
            old_price=float(old_price) if old_price else None,
            discount_percent=discount,
            rating=_as_float(product.get("reviewRating") or product.get("rating")),
            reviews_count=_as_int(product.get("feedbacks")),
            seller_name=product.get("supplier") or product.get("brand"),
            seller_rating=None,
            image_url=None,
            product_url=f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
            availability=True,
            delivery_info="Уточняется на Wildberries",
            collected_at=datetime.now(timezone.utc),
        )

    def _apply_filters(self, offers: list[MarketplaceOffer], params: SearchParams) -> list[MarketplaceOffer]:
        filters = params.filters
        result = offers
        if filters.min_rating is not None:
            result = [offer for offer in result if (offer.rating or 0) >= filters.min_rating]
        if filters.min_reviews is not None:
            result = [offer for offer in result if (offer.reviews_count or 0) >= filters.min_reviews]
        if filters.min_price is not None:
            result = [offer for offer in result if offer.price >= filters.min_price]
        if filters.max_price is not None:
            result = [offer for offer in result if offer.price <= filters.max_price]
        return result


class WildberriesAdapter(MarketplaceAdapter, RuntimeAwareAdapter):
    marketplace_name = "wildberries"

    def __init__(self) -> None:
        self._mock = WildberriesMockAdapter()
        self._http = WildberriesHttpAdapter()
        self.runtime = AdapterRuntime()

    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        mode = os.getenv("PARSER_MODE", "mock").lower()
        if mode == "mock":
            self.set_runtime("mock")
            return self._mock.search_products(params)

        fallback_detail = "live endpoint returned no offers"
        try:
            offers = self._http.search_products(params)
            if offers:
                self.set_runtime("live", f"{len(offers)} offers")
                return offers
            if mode == "real":
                self.set_runtime("failed", "live endpoint returned no offers")
                return []
        except AdapterUnavailableError as exc:
            fallback_detail = _compact_runtime_detail(str(exc))
            if mode == "real":
                self.set_runtime("failed", fallback_detail)
                raise

        self.set_runtime("fallback", fallback_detail)
        return self._mock.search_products(params)


def _wildberries_headers() -> dict[str, str]:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://www.wildberries.ru/",
        "User-Agent": os.getenv("PARSER_USER_AGENT")
        or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
    }


def _wildberries_search_urls(query: str) -> list[tuple[str, str]]:
    encoded_query = quote_plus(query.strip())
    dest = os.getenv("WILDBERRIES_DEST", "-1257786")
    common_params = (
        f"ab_testing=false&appType=1&curr=rub&dest={dest}&query={encoded_query}"
        "&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
    )
    return [
        ("v18", f"https://search.wb.ru/exactmatch/ru/common/v18/search?{common_params}"),
        ("v14", f"https://search.wb.ru/exactmatch/ru/common/v14/search?{common_params}"),
        ("v13", f"https://search.wb.ru/exactmatch/ru/common/v13/search?{common_params}"),
    ]


def _compact_runtime_detail(detail: str, limit: int = 160) -> str:
    normalized = " ".join(detail.split())
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 3]}..."


def _extract_price(product: dict) -> float | None:
    for key in ("salePriceU", "salePrice", "priceU", "price"):
        value = _as_float(product.get(key))
        if value is None:
            continue
        return value / 100 if key.endswith("U") else value
    sizes = product.get("sizes") or []
    for size in sizes:
        price_data = size.get("price") or {}
        value = _as_float(price_data.get("total") or price_data.get("product") or price_data.get("basic"))
        if value:
            return value / 100
    return None


def _extract_old_price(product: dict) -> float | None:
    for key in ("priceU", "price"):
        value = _as_float(product.get(key))
        if value:
            return value / 100 if key.endswith("U") else value
    return None


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
