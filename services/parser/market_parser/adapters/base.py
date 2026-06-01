from abc import ABC, abstractmethod

from market_parser.models import MarketplaceOffer, SearchParams


class MarketplaceAdapter(ABC):
    marketplace_name: str

    @abstractmethod
    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        raise NotImplementedError
