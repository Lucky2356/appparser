from market_parser.adapters.base import MarketplaceAdapter
from market_parser.adapters.ozon import OzonAdapter
from market_parser.adapters.wildberries import WildberriesAdapter


def get_adapters() -> dict[str, MarketplaceAdapter]:
    adapters: list[MarketplaceAdapter] = [OzonAdapter(), WildberriesAdapter()]
    return {adapter.marketplace_name: adapter for adapter in adapters}
