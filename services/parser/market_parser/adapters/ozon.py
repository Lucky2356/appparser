from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup

from market_parser.adapters.base import MarketplaceAdapter
from market_parser.adapters.mock_base import BaseMockMarketplaceAdapter
from market_parser.adapters.runtime import AdapterRuntime, RuntimeAwareAdapter
from market_parser.errors import AdapterUnavailableError
from market_parser.models import MarketplaceOffer, SearchParams


OZON_BASE_URL = "https://www.ozon.ru"
PRICE_RE = re.compile(r"(?<!\d)(\d[\d\s]{1,12})(?:\s*)(?:₽|руб)", re.IGNORECASE)
REVIEWS_RE = re.compile(r"(\d[\d\s]*)\s+(?:отзыв|отзыва|отзывов)", re.IGNORECASE)
RATING_RE = re.compile(r"(?<!\d)([1-5][,.]\d)(?!\d)")


class OzonMockAdapter(BaseMockMarketplaceAdapter):
    marketplace_name = "ozon"
    display_name = "Ozon"
    brand_color = "dbeafe"
    price_multiplier = 1.0

    def _product_url(self, external_id: str, query: str) -> str:
        return f"{OZON_BASE_URL}/search/?text={quote_plus(query)}&from_global=true&mock_id={external_id}"


class OzonHttpAdapter(MarketplaceAdapter):
    marketplace_name = "ozon"

    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        response = self._fetch_search_page(params.query)
        html = response.text

        if response.status_code in {403, 429} or _is_antibot_page(html):
            raise AdapterUnavailableError(
                self.marketplace_name,
                f"Ozon endpoint unavailable: HTTP {response.status_code}, anti-bot challenge",
            )
        if response.status_code >= 400:
            raise AdapterUnavailableError(self.marketplace_name, f"Ozon endpoint unavailable: HTTP {response.status_code}")

        soup = BeautifulSoup(html, "html.parser")
        offers = _extract_jsonld_offers(soup, params)
        if not offers:
            offers = _extract_dom_offers(soup, params)

        filtered = _apply_filters(offers, params)
        if not filtered:
            raise AdapterUnavailableError(self.marketplace_name, "Ozon endpoint returned no product cards")
        return filtered[:40]

    def _fetch_search_page(self, query: str) -> httpx.Response:
        timeout = float(os.getenv("PARSER_HTTP_TIMEOUT_SECONDS", "8"))
        url = f"{OZON_BASE_URL}/search/?text={quote_plus(query.strip())}&from_global=true"

        with httpx.Client(headers=_ozon_headers(), follow_redirects=False, timeout=timeout) as client:
            response = client.get(url)
            if response.is_redirect and response.headers.get("location"):
                response = client.get(urljoin(str(response.url), response.headers["location"]))
            return response


class OzonAdapter(MarketplaceAdapter, RuntimeAwareAdapter):
    marketplace_name = "ozon"

    def __init__(self) -> None:
        self._mock = OzonMockAdapter()
        self._http = OzonHttpAdapter()
        self.runtime = AdapterRuntime()

    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        mode = os.getenv("PARSER_MODE", "mock").lower()
        if mode == "mock":
            self.set_runtime("mock")
            return self._mock.search_products(params)

        try:
            offers = self._http.search_products(params)
            if offers:
                self.set_runtime("live", f"{len(offers)} offers")
                return offers
            if mode == "real":
                self.set_runtime("failed", "live endpoint returned no offers")
                return []
        except AdapterUnavailableError as exc:
            detail = _compact_runtime_detail(str(exc))
            if mode == "real":
                self.set_runtime("failed", detail)
                raise
            self.set_runtime("fallback", detail)
            return self._mock.search_products(params)

        self.set_runtime("fallback", "live endpoint returned no offers")
        return self._mock.search_products(params)


def _ozon_headers() -> dict[str, str]:
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "User-Agent": os.getenv("PARSER_USER_AGENT")
        or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
    }


def _is_antibot_page(html: str) -> bool:
    lowered = html.lower()
    return "antibot challenge" in lowered or "abt-challenge" in lowered or "captcha" in lowered


def _extract_jsonld_offers(soup: BeautifulSoup, params: SearchParams) -> list[MarketplaceOffer]:
    offers: list[MarketplaceOffer] = []
    seen: set[str] = set()
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text("", strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        for product in _walk_jsonld_products(payload):
            offer = _offer_from_jsonld_product(product, params.query)
            if not offer or offer.external_id in seen:
                continue
            seen.add(offer.external_id)
            offers.append(offer)
    return offers


def _walk_jsonld_products(node: Any) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    if isinstance(node, list):
        for item in node:
            products.extend(_walk_jsonld_products(item))
        return products
    if not isinstance(node, dict):
        return products

    node_type = node.get("@type")
    if node_type == "Product" or (isinstance(node_type, list) and "Product" in node_type):
        products.append(node)

    for key in ("@graph", "itemListElement", "item", "mainEntity", "about"):
        value = node.get(key)
        if value is not None:
            products.extend(_walk_jsonld_products(value))
    return products


def _offer_from_jsonld_product(product: dict[str, Any], query: str) -> MarketplaceOffer | None:
    title = _first_text(product.get("name"))
    offer_data = _first_mapping(product.get("offers"))
    price = _as_price(offer_data.get("price") or offer_data.get("lowPrice") or offer_data.get("highPrice"))
    product_url = urljoin(OZON_BASE_URL, _first_text(product.get("url")) or f"/search/?text={quote_plus(query)}")
    external_key = _ozon_external_key(product_url) or _first_text(product.get("sku") or product.get("mpn"))

    if not title or not price:
        return None

    rating_data = _first_mapping(product.get("aggregateRating"))
    availability = str(offer_data.get("availability", "")).lower()

    return MarketplaceOffer(
        external_id=f"ozon-{external_key or _stable_external_key(product_url, title)}",
        marketplace="ozon",
        title=title,
        price=price,
        old_price=None,
        discount_percent=None,
        rating=_as_float(rating_data.get("ratingValue")),
        reviews_count=_as_int(rating_data.get("reviewCount")),
        seller_name=_first_text(_first_mapping(offer_data.get("seller")).get("name")),
        seller_rating=None,
        image_url=_first_text(product.get("image")),
        product_url=product_url,
        availability="outofstock" not in availability,
        delivery_info="Уточняется на Ozon",
        collected_at=datetime.now(timezone.utc),
    )


def _extract_dom_offers(soup: BeautifulSoup, params: SearchParams) -> list[MarketplaceOffer]:
    offers: list[MarketplaceOffer] = []
    seen: set[str] = set()

    for anchor in soup.select('a[href*="/product/"]'):
        href = anchor.get("href")
        if not href:
            continue
        product_url = urljoin(OZON_BASE_URL, str(href))
        external_key = _ozon_external_key(product_url)
        if not external_key or external_key in seen:
            continue

        card = _best_card_node(anchor)
        text = card.get_text(" ", strip=True) if card else anchor.get_text(" ", strip=True)
        price = _find_price(text)
        title = _dom_title(anchor, card)
        if not title or not price:
            continue

        seen.add(external_key)
        offers.append(
            MarketplaceOffer(
                external_id=f"ozon-{external_key}",
                marketplace="ozon",
                title=title,
                price=price,
                old_price=None,
                discount_percent=None,
                rating=_find_rating(text),
                reviews_count=_find_reviews_count(text),
                seller_name=None,
                seller_rating=None,
                image_url=_dom_image_url(card),
                product_url=product_url,
                availability=True,
                delivery_info="Уточняется на Ozon",
                collected_at=datetime.now(timezone.utc),
            )
        )
    return offers


def _best_card_node(anchor: Any) -> Any:
    node = anchor
    best = anchor
    for _ in range(5):
        parent = getattr(node, "parent", None)
        if parent is None:
            break
        node = parent
        text = node.get_text(" ", strip=True)
        if "₽" in text or "руб" in text.lower():
            best = node
            break
        if len(text) > len(best.get_text(" ", strip=True)):
            best = node
    return best


def _dom_title(anchor: Any, card: Any) -> str | None:
    candidates = [anchor.get_text(" ", strip=True)]
    image = card.select_one("img[alt]") if card else None
    if image:
        candidates.append(str(image.get("alt", "")))
    if card:
        candidates.append(card.get_text(" ", strip=True))

    for candidate in candidates:
        normalized = _clean_dom_title(candidate)
        if len(normalized) >= 5:
            return normalized[:180]
    return None


def _clean_dom_title(text: str) -> str:
    without_prices = PRICE_RE.sub(" ", text)
    without_reviews = REVIEWS_RE.sub(" ", without_prices)
    return " ".join(without_reviews.split())


def _dom_image_url(card: Any) -> str | None:
    image = card.select_one("img[src]") if card else None
    if not image:
        return None
    return urljoin(OZON_BASE_URL, str(image.get("src")))


def _find_price(text: str) -> float | None:
    for match in PRICE_RE.finditer(text):
        price = _as_price(match.group(1))
        if price:
            return price
    return None


def _find_rating(text: str) -> float | None:
    match = RATING_RE.search(text)
    if not match:
        return None
    rating = _as_float(match.group(1).replace(",", "."))
    return rating if rating and 0 < rating <= 5 else None


def _find_reviews_count(text: str) -> int | None:
    match = REVIEWS_RE.search(text)
    return _as_int(match.group(1).replace(" ", "")) if match else None


def _apply_filters(offers: list[MarketplaceOffer], params: SearchParams) -> list[MarketplaceOffer]:
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


def _first_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        return _first_mapping(value[0]) if value else {}
    return value if isinstance(value, dict) else {}


def _first_text(value: Any) -> str | None:
    if isinstance(value, list):
        return _first_text(value[0]) if value else None
    if value is None:
        return None
    normalized = " ".join(str(value).split())
    return normalized or None


def _ozon_external_key(url: str) -> str | None:
    match = re.search(r"-(\d{5,})(?:[/?#]|$)", url)
    if match:
        return match.group(1)
    match = re.search(r"/product/[^/?#]*?(\d{5,})(?:[/?#]|$)", url)
    return match.group(1) if match else None


def _stable_external_key(url: str, title: str) -> str:
    return hashlib.sha1(f"{url}:{title}".encode("utf-8")).hexdigest()[:16]


def _as_price(value: Any) -> float | None:
    if value is None:
        return None
    normalized = re.sub(r"[^\d,.]", "", str(value)).replace(",", ".")
    if not normalized:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).replace(" ", ""))
    except (TypeError, ValueError):
        return None


def _compact_runtime_detail(detail: str, limit: int = 160) -> str:
    normalized = " ".join(detail.split())
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 3]}..."
