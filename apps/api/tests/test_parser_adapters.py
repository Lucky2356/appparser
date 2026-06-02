import httpx
import pytest

from app.searches.service import _should_fail_real_search
from market_parser.adapters.ozon import OzonAdapter, OzonHttpAdapter
from market_parser.adapters.wildberries import WildberriesAdapter
from market_parser.cache import OFFER_CACHE
from market_parser.errors import AdapterUnavailableError
from market_parser.models import MarketplaceOffer, ParserLogEntry, SearchParams
from market_parser.service import collect_offers


class FailingHttpAdapter:
    def __init__(self, marketplace: str) -> None:
        self.marketplace = marketplace

    def search_products(self, params: SearchParams):  # noqa: ARG002
        raise AdapterUnavailableError(self.marketplace, "blocked by source")


class EmptyHttpAdapter:
    def search_products(self, params: SearchParams):  # noqa: ARG002
        return []


class FixtureOzonHttpAdapter(OzonHttpAdapter):
    def __init__(self, html: str = "", status_code: int = 200, composer_payload: dict | None = None) -> None:
        self.html = html
        self.status_code = status_code
        self.composer_payload = composer_payload

    def _fetch_composer_payload(self, query: str) -> dict:  # noqa: ARG002
        if self.composer_payload is None:
            raise AdapterUnavailableError("ozon", "composer unavailable")
        return self.composer_payload

    def _fetch_search_page(self, query: str) -> httpx.Response:  # noqa: ARG002
        request = httpx.Request("GET", "https://www.ozon.ru/search/?text=phone")
        return httpx.Response(self.status_code, text=self.html, request=request)


def test_collect_offers_reports_mock_adapter_source(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PARSER_MODE", "mock")
    OFFER_CACHE.clear()

    result = collect_offers(SearchParams(query="runtime source smoke", marketplaces=["ozon", "wildberries"]))

    messages = {(log.marketplace, log.message) for log in result.logs}
    assert ("ozon", "Adapter source: mock") in messages
    assert ("wildberries", "Adapter source: mock") in messages


def test_ozon_hybrid_falls_back_when_live_source_is_unavailable(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PARSER_MODE", "hybrid")
    adapter = OzonAdapter()
    adapter._http = FailingHttpAdapter("ozon")

    offers = adapter.search_products(SearchParams(query="phone", marketplaces=["ozon"]))

    assert offers
    assert adapter.runtime.source == "fallback"
    assert "blocked by source" in adapter.runtime.detail


def test_wildberries_real_mode_surfaces_live_failures(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PARSER_MODE", "real")
    adapter = WildberriesAdapter()
    adapter._http = FailingHttpAdapter("wildberries")

    with pytest.raises(AdapterUnavailableError):
        adapter.search_products(SearchParams(query="phone", marketplaces=["wildberries"]))

    assert adapter.runtime.source == "failed"
    assert "blocked by source" in adapter.runtime.detail


def test_wildberries_hybrid_falls_back_when_live_source_is_empty(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PARSER_MODE", "hybrid")
    adapter = WildberriesAdapter()
    adapter._http = EmptyHttpAdapter()

    offers = adapter.search_products(SearchParams(query="phone", marketplaces=["wildberries"]))

    assert offers
    assert adapter.runtime.source == "fallback"


def test_ozon_http_adapter_extracts_jsonld_products():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Phone Pro 256",
            "sku": "123456789",
            "image": "https://cdn.example.test/phone.webp",
            "url": "/product/phone-pro-123456789/",
            "aggregateRating": {"ratingValue": "4.8", "reviewCount": "321"},
            "offers": {
              "@type": "Offer",
              "price": "42990",
              "availability": "https://schema.org/InStock",
              "seller": {"name": "Official Store"}
            }
          }
        </script>
      </head>
    </html>
    """

    offers = FixtureOzonHttpAdapter(html).search_products(SearchParams(query="phone", marketplaces=["ozon"]))

    assert len(offers) == 1
    assert offers[0].external_id == "ozon-123456789"
    assert offers[0].price == 42990
    assert offers[0].rating == 4.8
    assert offers[0].reviews_count == 321


def test_ozon_http_adapter_extracts_composer_products():
    payload = {
        "widgetStates": {
            "searchResultsV2-1": """
            {
              "items": [
                {
                  "action": {"link": "/product/phone-pro-987654321/"},
                  "mainState": [
                    {"atom": {"textAtom": {"text": "Phone Pro Max"}}},
                    {"atom": {"priceV2": {"price": "51 990 ₽"}}},
                    {"atom": {"textAtom": {"text": "4,9 777 отзывов"}}}
                  ],
                  "tileImage": {"image": "https://cdn1.ozone.ru/s3/phone.webp"}
                }
              ]
            }
            """
        }
    }

    offers = FixtureOzonHttpAdapter(composer_payload=payload).search_products(
        SearchParams(query="phone", marketplaces=["ozon"])
    )

    assert len(offers) == 1
    assert offers[0].external_id == "ozon-987654321"
    assert offers[0].title == "Phone Pro Max"
    assert offers[0].price == 51990
    assert offers[0].rating == 4.9
    assert offers[0].reviews_count == 777


def test_real_search_fails_when_live_sources_return_only_errors(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PARSER_MODE", "real")
    logs = [
        ParserLogEntry(
            marketplace="ozon",
            level="error",
            message="Adapter source: failed (anti-bot challenge)",
        )
    ]

    assert _should_fail_real_search([], logs)


def test_real_search_stays_completed_when_at_least_one_live_offer(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PARSER_MODE", "real")
    offer = MarketplaceOffer(
        external_id="ozon-1",
        marketplace="ozon",
        title="Phone",
        price=1000,
        product_url="https://www.ozon.ru/product/phone-1/",
    )

    assert not _should_fail_real_search([offer], [])
