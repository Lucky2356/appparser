from fastapi import APIRouter

from app.schemas import CamelModel


class MarketplaceRead(CamelModel):
    id: str
    name: str
    enabled: bool
    is_mock: bool


router = APIRouter(tags=["marketplaces"])


@router.get("/marketplaces", response_model=list[MarketplaceRead])
def list_marketplaces() -> list[MarketplaceRead]:
    return [
        MarketplaceRead(id="ozon", name="Ozon", enabled=True, is_mock=True),
        MarketplaceRead(id="wildberries", name="Wildberries", enabled=True, is_mock=True),
    ]
