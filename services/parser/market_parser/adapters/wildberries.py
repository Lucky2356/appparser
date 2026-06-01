from market_parser.adapters.mock_base import BaseMockMarketplaceAdapter


class WildberriesAdapter(BaseMockMarketplaceAdapter):
    marketplace_name = "wildberries"
    display_name = "Wildberries"
    brand_color = "fce7f3"
    price_multiplier = 0.97

    def _product_url(self, external_id: str, query: str) -> str:
        from urllib.parse import quote_plus

        return f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote_plus(query)}&mock_id={external_id}"
