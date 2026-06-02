from __future__ import annotations

import json
import os
import time
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
        rate_limit_retries = int(os.getenv("PARSER_WB_429_RETRIES", "1"))

        with httpx.Client(
            headers=_wildberries_headers(),
            follow_redirects=True,
            timeout=timeout,
            proxy=_http_proxy(),
        ) as client:
            for version, url in _wildberries_search_urls(params.query):
                try:
                    response = _get_with_rate_limit_retries(client, url, rate_limit_retries)
                    if response.status_code == 429:
                        if _browser_fallback_enabled():
                            try:
                                payload = _fetch_payload_with_browser(url, timeout)
                            except AdapterUnavailableError as exc:
                                errors.append(f"{version}: rate limited after retry; browser {exc.message}")
                                continue
                        else:
                            errors.append(f"{version}: rate limited after retry")
                            continue
                    else:
                        response.raise_for_status()
                        payload = response.json()
                except httpx.HTTPStatusError as exc:
                    errors.append(f"{version}: HTTP {exc.response.status_code}")
                    continue
                except (httpx.HTTPError, ValueError) as exc:
                    errors.append(f"{version}: {exc.__class__.__name__}")
                    continue

                products = _extract_products(payload)
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
            image_url=_wildberries_image_url(product_id),
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
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://www.wildberries.ru/",
        "User-Agent": os.getenv("PARSER_USER_AGENT")
        or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        ),
    }
    cookies = os.getenv("WILDBERRIES_COOKIES", "").strip()
    if cookies:
        headers["Cookie"] = cookies
    return headers


def _wildberries_search_urls(query: str) -> list[tuple[str, str]]:
    encoded_query = quote_plus(query.strip())
    dest = os.getenv("WILDBERRIES_DEST", "-1257786")
    common_params = (
        f"ab_testing=false&appType=1&curr=rub&dest={dest}&query={encoded_query}"
        "&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
    )
    return [
        ("v5", f"https://search.wb.ru/exactmatch/ru/common/v5/search?{common_params}"),
        ("v4", f"https://search.wb.ru/exactmatch/ru/common/v4/search?{common_params}"),
        ("v13", f"https://search.wb.ru/exactmatch/ru/common/v13/search?{common_params}"),
    ]


def _http_proxy() -> str | None:
    return os.getenv("PARSER_HTTP_PROXY") or None


def _browser_fallback_enabled() -> bool:
    return os.getenv("PARSER_BROWSER_FALLBACK", "true").lower() not in {"0", "false", "no"}


def _extract_products(payload: object) -> list | None:
    if not isinstance(payload, dict):
        return None

    products = payload.get("products")
    if isinstance(products, list):
        return products

    data = payload.get("data")
    if isinstance(data, dict):
        products = data.get("products")
        if isinstance(products, list):
            return products
    return None


def _get_with_rate_limit_retries(client: httpx.Client, url: str, retries: int) -> httpx.Response:
    response = client.get(url)
    for _ in range(max(0, retries)):
        if response.status_code != 429:
            break
        _sleep_after_rate_limit(response)
        response = client.get(url)
    return response


def _fetch_payload_with_browser(url: str, timeout: float) -> dict:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise AdapterUnavailableError("wildberries", "Playwright is not installed") from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(
                    extra_http_headers=_wildberries_browser_headers(),
                    locale="ru-RU",
                    user_agent=_wildberries_headers()["User-Agent"],
                )
                status_code = 0
                body_text = ""
                for attempt in range(_browser_rate_limit_retries() + 1):
                    response = page.goto(url, wait_until="domcontentloaded", timeout=max(5000, timeout * 1000))
                    status_code = response.status if response else 0
                    body_text = page.locator("body").inner_text(timeout=5000)
                    if status_code != 429 or attempt >= _browser_rate_limit_retries():
                        break
                    time.sleep(_browser_rate_limit_delay())
                if status_code in {403, 429}:
                    raise AdapterUnavailableError("wildberries", f"browser endpoint HTTP {status_code}")
                if status_code >= 400:
                    raise AdapterUnavailableError("wildberries", f"browser endpoint HTTP {status_code}")
                payload = json.loads(body_text)
                if not isinstance(payload, dict):
                    raise AdapterUnavailableError("wildberries", "browser endpoint returned unexpected payload")
                return payload
            finally:
                browser.close()
    except json.JSONDecodeError as exc:
        raise AdapterUnavailableError("wildberries", "browser endpoint returned non-JSON payload") from exc
    except PlaywrightError as exc:
        raise AdapterUnavailableError("wildberries", f"browser endpoint {exc.__class__.__name__}") from exc


def _wildberries_browser_headers() -> dict[str, str]:
    headers = {
        key: value
        for key, value in _wildberries_headers().items()
        if key.lower() not in {"user-agent"}
    }
    return headers


def _browser_rate_limit_retries() -> int:
    return int(os.getenv("PARSER_BROWSER_429_RETRIES", "1"))


def _browser_rate_limit_delay() -> float:
    return float(os.getenv("PARSER_BROWSER_429_DELAY_SECONDS", "10"))


def _sleep_after_rate_limit(response: httpx.Response) -> None:
    retry_after = (
        _as_float(response.headers.get("X-Ratelimit-Retry"))
        or _as_float(response.headers.get("X-Ratelimit-Reset"))
        or _as_float(response.headers.get("Retry-After"))
    )
    delay = retry_after if retry_after and retry_after > 0 else float(os.getenv("PARSER_WB_429_DELAY_SECONDS", "10"))
    time.sleep(min(delay, 30.0))


def _wildberries_image_url(product_id: object) -> str | None:
    product_number = _as_int(product_id)
    if product_number is None:
        return None
    vol = product_number // 100000
    part = product_number // 1000
    return f"https://basket-{_wildberries_basket(vol)}.wbbasket.ru/vol{vol}/part{part}/{product_number}/images/big/1.webp"


def _wildberries_basket(vol: int) -> str:
    ranges = [
        (143, "01"),
        (287, "02"),
        (431, "03"),
        (719, "04"),
        (1007, "05"),
        (1061, "06"),
        (1115, "07"),
        (1169, "08"),
        (1313, "09"),
        (1601, "10"),
        (1655, "11"),
        (1919, "12"),
        (2045, "13"),
        (2189, "14"),
        (2405, "15"),
    ]
    for max_vol, basket in ranges:
        if vol <= max_vol:
            return basket
    return "16"


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
