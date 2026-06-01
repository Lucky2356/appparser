from datetime import datetime

from app.schemas import CamelModel


class FavoriteCreate(CamelModel):
    offer_id: str


class FavoriteRead(CamelModel):
    id: str
    offer_id: str | None = None
    marketplace: str
    external_id: str
    title: str
    price: float
    rating: float | None = None
    image_url: str | None = None
    product_url: str
    score: float | None = None
    created_at: datetime
