from datetime import datetime

from pydantic import Field

from app.schemas import CamelModel


class SearchFilters(CamelModel):
    min_rating: float | None = Field(default=None, ge=0, le=5)
    min_reviews: int | None = Field(default=None, ge=0)
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)


class SearchCreate(CamelModel):
    query: str = Field(min_length=2, max_length=255)
    marketplaces: list[str] = Field(min_length=1)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    sort: str = "best_value"


class SearchCreated(CamelModel):
    search_id: str
    status: str


class SearchRead(CamelModel):
    id: str
    query: str
    marketplaces: list[str]
    filters: dict
    sort: str
    status: str
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class OfferRead(CamelModel):
    id: str
    external_id: str
    marketplace: str
    title: str
    price: float
    old_price: float | None = None
    discount_percent: int | None = None
    rating: float | None = None
    reviews_count: int | None = None
    seller_name: str | None = None
    seller_rating: float | None = None
    image_url: str | None = None
    product_url: str
    availability: bool
    delivery_info: str | None = None
    collected_at: datetime
    score: float
    score_reasons: list[str]


class SearchResults(CamelModel):
    search_id: str
    status: str
    results: list[OfferRead]
