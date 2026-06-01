import os

from fastapi import APIRouter

from app.schemas import CamelModel


class MarketplaceRead(CamelModel):
    id: str
    name: str
    enabled: bool
    is_mock: bool
    source_mode: str


router = APIRouter(tags=["marketplaces"])


@router.get("/marketplaces", response_model=list[MarketplaceRead])
def list_marketplaces() -> list[MarketplaceRead]:
    source_mode = os.getenv("PARSER_MODE", "mock").lower()
    is_mock = source_mode == "mock"
    return [
        MarketplaceRead(id="ozon", name="Ozon", enabled=True, is_mock=is_mock, source_mode=source_mode),
        MarketplaceRead(id="wildberries", name="Wildberries", enabled=True, is_mock=is_mock, source_mode=source_mode),
    ]
