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
REVIEWS_RE = re.compile(r"(?<![\d,])(\d[\d\s]*)\s+(?:отзыв|отзыва|отзывов)", re.IGNORECASE)
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
        errors: list[str] = []

        try:
            payload = self._fetch_composer_payload(params.query)
            offers = _extract_composer_offers(payload, params)
            filtered = _apply_filters(offers, params)
            if filtered:
                return filtered[:40]
            errors.append("composer endpoint returned no product cards")
        except AdapterUnavailableError as exc:
            errors.append(str(exc))

        try:
            response = self._fetch_search_page(params.query)
            html = response.text

            if response.status_code in {403, 429} or _is_antibot_page(html):
                errors.append(f"HTML endpoint HTTP {response.status_code}, anti-bot challenge")
            elif response.status_code >= 400:
                errors.append(f"HTML endpoint HTTP {response.status_code}")
            else:
                soup = BeautifulSoup(html, "html.parser")
                offers = _extract_jsonld_offers(soup, params)
                if not offers:
                    offers = _extract_dom_offers(soup, params)

                filtered = _apply_filters(offers, params)
                if filtered:
                    return filtered[:40]
                errors.append("HTML endpoint returned no product cards")
        except httpx.HTTPError as exc:
            errors.append(f"HTML endpoint {exc.__class__.__name__}")

        if _browser_fallback_enabled():
            try:
                html = _fetch_search_page_with_browser(params.query)
                soup = BeautifulSoup(html, "html.parser")
                offers = _extract_jsonld_offers(soup, params)
                if not offers:
                    offers = _extract_dom_offers(soup, params)

                filtered = _apply_filters(offers, params)
                if filtered:
                    return filtered[:40]
                errors.append("browser endpoint returned no product cards")
            except AdapterUnavailableError as exc:
                errors.append(str(exc))

        raise AdapterUnavailableError(self.marketplace_name, f"Ozon endpoint unavailable: {'; '.join(errors[:4])}")

    def _fetch_composer_payload(self, query: str) -> dict[str, Any]:
        timeout = float(os.getenv("PARSER_HTTP_TIMEOUT_SECONDS", "8"))
        path = _ozon_search_path(query)
        url = f"{OZON_BASE_URL}/api/composer-api.bx/page/json/v2?url={path}"

        with httpx.Client(headers=_ozon_headers(), follow_redirects=False, timeout=timeout, proxy=_http_proxy()) as client:
            response = _get_with_one_redirect(client, url)

        if response.status_code in {403, 429} or _is_antibot_page(response.text):
            raise AdapterUnavailableError(
                self.marketplace_name,
                f"composer endpoint HTTP {response.status_code}, anti-bot challenge",
            )
        if response.status_code >= 400:
            raise AdapterUnavailableError(self.marketplace_name, f"composer endpoint HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise AdapterUnavailableError(self.marketplace_name, "composer endpoint returned non-JSON payload") from exc

        if not isinstance(payload, dict):
            raise AdapterUnavailableError(self.marketplace_name, "composer endpoint returned unexpected payload")
        return payload

    def _fetch_search_page(self, query: str) -> httpx.Response:
        timeout = float(os.getenv("PARSER_HTTP_TIMEOUT_SECONDS", "8"))
        url = f"{OZON_BASE_URL}{_ozon_search_path(query)}"

        with httpx.Client(headers=_ozon_headers(), follow_redirects=False, timeout=timeout, proxy=_http_proxy()) as client:
            return _get_with_one_redirect(client, url)


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
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "User-Agent": os.getenv("PARSER_USER_AGENT")
        or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        ),
    }
    cookies = os.getenv("OZON_COOKIES", "").strip()
    if cookies:
        headers["Cookie"] = cookies
    return headers


def _ozon_search_path(query: str) -> str:
    return f"/search/?text={quote_plus(query.strip())}&from_global=true"


def _http_proxy() -> str | None:
    return os.getenv("PARSER_HTTP_PROXY") or None


def _browser_fallback_enabled() -> bool:
    return os.getenv("PARSER_BROWSER_FALLBACK", "true").lower() not in {"0", "false", "no"}


def _get_with_one_redirect(client: httpx.Client, url: str) -> httpx.Response:
    response = client.get(url)
    if response.is_redirect and response.headers.get("location"):
        return client.get(urljoin(str(response.url), response.headers["location"]))
    return response


def _is_antibot_page(html: str) -> bool:
    lowered = html.lower()
    return "antibot challenge" in lowered or "abt-challenge" in lowered or "captcha" in lowered


def _fetch_search_page_with_browser(query: str) -> str:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise AdapterUnavailableError("ozon", "browser endpoint requires Playwright") from exc

    timeout_ms = int(float(os.getenv("PARSER_HTTP_TIMEOUT_SECONDS", "8")) * 1000)
    proxy = _http_proxy()
    launch_options: dict[str, Any] = {"headless": True}
    if proxy:
        launch_options["proxy"] = {"server": proxy}

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(**launch_options)
            try:
                page = browser.new_page(
                    extra_http_headers=_ozon_browser_headers(),
                    locale="ru-RU",
                    user_agent=_ozon_headers()["User-Agent"],
                )
                response = page.goto(
                    f"{OZON_BASE_URL}{_ozon_search_path(query)}",
                    wait_until="domcontentloaded",
                    timeout=max(5000, timeout_ms),
                )
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except PlaywrightTimeoutError:
                    pass
                status_code = response.status if response else 0
                html = page.content()
                if status_code in {403, 429} or _is_antibot_page(html):
                    raise AdapterUnavailableError("ozon", f"browser endpoint HTTP {status_code}, anti-bot challenge")
                if status_code >= 400:
                    raise AdapterUnavailableError("ozon", f"browser endpoint HTTP {status_code}")
                return html
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise AdapterUnavailableError("ozon", f"browser endpoint {exc.__class__.__name__}") from exc


def _ozon_browser_headers() -> dict[str, str]:
    return {key: value for key, value in _ozon_headers().items() if key.lower() != "user-agent"}


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


def _extract_composer_offers(payload: dict[str, Any], params: SearchParams) -> list[MarketplaceOffer]:
    offers: list[MarketplaceOffer] = []
    seen: set[str] = set()

    for node in _walk_composer_nodes(payload):
        product_url = _first_product_url(node)
        if not product_url:
            continue
        external_key = _ozon_external_key(product_url)
        if not external_key or external_key in seen:
            continue

        title = _composer_title(node)
        price = _composer_price(node)
        if not title or not price:
            continue

        seen.add(external_key)
        text = _composer_text(node)
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
                image_url=_composer_image_url(node),
                product_url=product_url,
                availability=True,
                delivery_info="Уточняется на Ozon",
                collected_at=datetime.now(timezone.utc),
            )
        )
    return offers


def _walk_composer_nodes(node: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    stack = [node]
    decoded_strings = 0

    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            found.append(current)
            stack.extend(current.values())
            continue
        if isinstance(current, list):
            stack.extend(current)
            continue
        if isinstance(current, str) and decoded_strings < 100:
            stripped = current.strip()
            if stripped[:1] in {"{", "["}:
                try:
                    stack.append(json.loads(stripped))
                    decoded_strings += 1
                except json.JSONDecodeError:
                    pass
    return found


def _first_product_url(node: Any) -> str | None:
    for value in _walk_scalar_values(node):
        if not isinstance(value, str) or "/product/" not in value:
            continue
        normalized = value.split("?")[0]
        return urljoin(OZON_BASE_URL, normalized)
    return None


def _composer_title(node: dict[str, Any]) -> str | None:
    for key, value in _walk_key_values(node):
        if not isinstance(value, str):
            continue
        lowered_key = key.lower()
        if "title" not in lowered_key and "name" not in lowered_key and lowered_key != "text":
            continue
        if PRICE_RE.search(value) or "отзыв" in value.lower():
            continue
        title = _clean_dom_title(value)
        if _looks_like_title(title):
            return title[:180]
    return None


def _composer_price(node: dict[str, Any]) -> float | None:
    for value in _walk_scalar_values(node):
        if isinstance(value, str):
            price = _find_price(value)
            if price:
                return price

    for key, value in _walk_key_values(node):
        if "price" not in key.lower() or not isinstance(value, (int, float, str)):
            continue
        price = _as_price(value)
        if price and 10 <= price <= 10_000_000:
            return price / 100 if price > 1_000_000 else price
    return None


def _composer_image_url(node: dict[str, Any]) -> str | None:
    for value in _walk_scalar_values(node):
        if not isinstance(value, str):
            continue
        if "cdn" in value and ("ozone.ru" in value or "ozonusercontent.com" in value):
            return urljoin(OZON_BASE_URL, value)
        if re.search(r"\.(?:webp|jpg|jpeg|png)(?:[?#]|$)", value):
            return urljoin(OZON_BASE_URL, value)
    return None


def _composer_text(node: dict[str, Any]) -> str:
    values = [value for value in _walk_scalar_values(node) if isinstance(value, str)]
    return " ".join(values[:80])


def _walk_key_values(node: Any) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    stack = [node]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                items.append((str(key), value))
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return items


def _walk_scalar_values(node: Any) -> list[Any]:
    values: list[Any] = []
    stack = [node]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
        else:
            values.append(current)
    return values


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


def _looks_like_title(text: str) -> bool:
    if len(text) < 5 or len(text) > 220:
        return False
    lowered = text.lower()
    ignored_fragments = ("₽", "руб", "отзыв", "доставка", "в корзину", "ozon")
    return not any(fragment in lowered for fragment in ignored_fragments)


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
