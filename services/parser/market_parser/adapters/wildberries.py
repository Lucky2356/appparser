from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from market_parser.adapters.base import MarketplaceAdapter
from market_parser.adapters.mock_base import BaseMockMarketplaceAdapter
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
        url = (
            "https://search.wb.ru/exactmatch/ru/common/v18/search"
            f"?ab_testing=false&appType=1&curr=rub&dest=-1257786"
            f"&query={quote_plus(params.query)}&resultset=catalog&sort=popular&spp=30"
            "&suppressSpellcheck=false"
        )
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Appsparcer/0.1 (+local development; respectful rate limited requests)",
            },
        )

        try:
            with urlopen(request, timeout=float(os.getenv("PARSER_HTTP_TIMEOUT_SECONDS", "8"))) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise AdapterUnavailableError(self.marketplace_name, f"Wildberries endpoint unavailable: {exc}") from exc

        products = payload.get("data", {}).get("products", [])
        offers = [self._normalize_product(product) for product in products[:40]]
        offers = [offer for offer in offers if offer is not None]
        return self._apply_filters(offers, params)

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


class WildberriesAdapter(MarketplaceAdapter):
    marketplace_name = "wildberries"

    def __init__(self) -> None:
        self._mock = WildberriesMockAdapter()
        self._http = WildberriesHttpAdapter()

    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        mode = os.getenv("PARSER_MODE", "mock").lower()
        if mode == "mock":
            return self._mock.search_products(params)

        try:
            offers = self._http.search_products(params)
            if offers:
                return offers
            if mode == "real":
                return []
        except AdapterUnavailableError:
            if mode == "real":
                raise

        return self._mock.search_products(params)


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
