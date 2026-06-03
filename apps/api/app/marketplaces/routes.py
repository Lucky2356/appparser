import os

from fastapi import APIRouter

from app.schemas import CamelModel


class MarketplaceRead(CamelModel):
    id: str
    name: str
    enabled: bool
    is_mock: bool
    source_mode: str
    access_configured: bool
    browser_fallback_enabled: bool
    status_note: str


router = APIRouter(tags=["marketplaces"])


@router.get("/marketplaces", response_model=list[MarketplaceRead])
def list_marketplaces() -> list[MarketplaceRead]:
    source_mode = os.getenv("PARSER_MODE", "mock").lower()
    is_mock = source_mode == "mock"
    browser_fallback_enabled = os.getenv("PARSER_BROWSER_FALLBACK", "true").lower() not in {"0", "false", "no"}
    proxy_configured = bool(os.getenv("PARSER_HTTP_PROXY", "").strip())
    ozon_access_configured = proxy_configured or bool(os.getenv("OZON_COOKIES", "").strip())
    wildberries_access_configured = proxy_configured or browser_fallback_enabled or bool(os.getenv("WILDBERRIES_COOKIES", "").strip())
    return [
        MarketplaceRead(
            id="ozon",
            name="Ozon",
            enabled=True,
            is_mock=is_mock,
            source_mode=source_mode,
            access_configured=is_mock or source_mode == "hybrid" or ozon_access_configured,
            browser_fallback_enabled=browser_fallback_enabled,
            status_note=(
                "configured"
                if is_mock or source_mode == "hybrid" or ozon_access_configured
                else "requires cookies or proxy for stable real access"
            ),
        ),
        MarketplaceRead(
            id="wildberries",
            name="Wildberries",
            enabled=True,
            is_mock=is_mock,
            source_mode=source_mode,
            access_configured=is_mock or source_mode == "hybrid" or wildberries_access_configured,
            browser_fallback_enabled=browser_fallback_enabled,
            status_note="browser fallback enabled" if browser_fallback_enabled and not is_mock else "configured",
        ),
    ]
