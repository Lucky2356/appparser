from datetime import datetime

from pydantic import Field

from app.schemas import CamelModel


class TrackedProductCreate(CamelModel):
    marketplace: str
    title: str = Field(min_length=2, max_length=500)
    product_url: str = Field(min_length=8)
    target_price: float | None = Field(default=None, ge=0)
    last_price: float | None = Field(default=None, ge=0)


class TrackedProductFromOffer(CamelModel):
    offer_id: str
    target_price: float | None = Field(default=None, ge=0)


class TrackedProductRead(CamelModel):
    id: str
    marketplace: str
    title: str
    product_url: str
    target_price: float | None = None
    last_price: float | None = None
    last_checked_at: datetime | None = None
    created_at: datetime


class PriceHistoryRead(CamelModel):
    id: str
    tracked_product_id: str
    price: float
    collected_at: datetime
