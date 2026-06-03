from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response


router = APIRouter(tags=["images"])

ALLOWED_IMAGE_HOST_SUFFIXES = (
    "wbbasket.ru",
    "wbstatic.net",
    "wildberries.ru",
    "ozone.ru",
    "ozonusercontent.com",
    "placehold.co",
)


@router.get("/images/proxy")
def proxy_image(url: str = Query(min_length=8, max_length=2048)) -> Response:
    normalized_url = url.strip()
    if not _is_allowed_image_url(normalized_url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image host is not allowed")

    try:
        with httpx.Client(
            follow_redirects=True,
            headers=_image_request_headers(normalized_url),
            timeout=float(os.getenv("IMAGE_PROXY_TIMEOUT_SECONDS", "8")),
        ) as client:
            response = client.get(normalized_url)
            if not _is_allowed_image_url(str(response.url)):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image redirect host is not allowed")
            response.raise_for_status()
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Image source HTTP {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Image source is unavailable") from exc

    content_type = (response.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Source is not an image")

    max_bytes = int(os.getenv("IMAGE_PROXY_MAX_BYTES", str(5 * 1024 * 1024)))
    if len(response.content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large")

    cache_seconds = int(os.getenv("IMAGE_PROXY_CACHE_SECONDS", "86400"))
    return Response(
        content=response.content,
        media_type=content_type,
        headers={"Cache-Control": f"public, max-age={cache_seconds}"},
    )


def _is_allowed_image_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower().rstrip(".")
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_IMAGE_HOST_SUFFIXES)


def _image_request_headers(url: str) -> dict[str, str]:
    host = urlparse(url).hostname or ""
    headers = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "User-Agent": os.getenv("PARSER_USER_AGENT")
        or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        ),
    }
    if "wbbasket.ru" in host or "wildberries.ru" in host or "wbstatic.net" in host:
        headers["Referer"] = "https://www.wildberries.ru/"
    elif "ozone.ru" in host or "ozonusercontent.com" in host:
        headers["Referer"] = "https://www.ozon.ru/"
    return headers
