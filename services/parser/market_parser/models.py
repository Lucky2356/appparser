from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class SearchFilters:
    min_rating: float | None = None
    min_reviews: int | None = None
    min_price: float | None = None
    max_price: float | None = None


@dataclass(slots=True)
class SearchParams:
    query: str
    marketplaces: list[str]
    filters: SearchFilters = field(default_factory=SearchFilters)
    sort: str = "best_value"


@dataclass(slots=True)
class MarketplaceOffer:
    external_id: str
    marketplace: str
    title: str
    price: float
    product_url: str
    availability: bool = True
    old_price: float | None = None
    discount_percent: int | None = None
    rating: float | None = None
    reviews_count: int | None = None
    seller_name: str | None = None
    seller_rating: float | None = None
    image_url: str | None = None
    delivery_info: str | None = None
    collected_at: datetime = field(default_factory=utc_now)
    score: float = 0
    score_reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParserLogEntry:
    marketplace: str
    level: str
    message: str


@dataclass(slots=True)
class ParserResult:
    offers: list[MarketplaceOffer]
    logs: list[ParserLogEntry]
