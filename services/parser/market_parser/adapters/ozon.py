from market_parser.adapters.mock_base import BaseMockMarketplaceAdapter


class OzonAdapter(BaseMockMarketplaceAdapter):
    marketplace_name = "ozon"
    display_name = "Ozon"
    brand_color = "dbeafe"
    price_multiplier = 1.0

    def _product_url(self, external_id: str, query: str) -> str:
        from urllib.parse import quote_plus

        return f"https://www.ozon.ru/search/?text={quote_plus(query)}&from_global=true&mock_id={external_id}"
