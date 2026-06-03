import os
from pathlib import Path

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
    proxy_configured = _has_env_value("PARSER_HTTP_PROXY")
    ozon_access_configured = proxy_configured or _has_env_value("OZON_COOKIES") or _env_file_exists(
        "OZON_COOKIES_FILE",
        "OZON_STORAGE_STATE_FILE",
    )
    wildberries_access_configured = (
        proxy_configured
        or browser_fallback_enabled
        or _has_env_value("WILDBERRIES_COOKIES", "WILDBERRIES_COOKIES_FILE", "WILDBERRIES_STORAGE_STATE_FILE")
    )
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
                else "requires Ozon session cookies, storage state, or proxy for stable real access"
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


def _has_env_value(*names: str) -> bool:
    return any(bool(os.getenv(name, "").strip()) for name in names)


def _env_file_exists(*names: str) -> bool:
    for name in names:
        raw = os.getenv(name, "").strip()
        if raw and Path(raw).is_file():
            return True
    return False
