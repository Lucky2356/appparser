from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def cookie_header_from_sources(
    cookie_env: str,
    cookie_file_env: str,
    storage_state_env: str,
    domain_hint: str,
) -> str | None:
    raw = os.getenv(cookie_env, "").strip()
    if raw:
        return raw

    file_value = _read_env_file(cookie_file_env)
    if file_value:
        return file_value

    state_path = storage_state_path(storage_state_env)
    if not state_path:
        return None
    return _cookie_header_from_storage_state(state_path, domain_hint)


def storage_state_path(env_name: str) -> str | None:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return None
    path = Path(raw)
    return str(path) if path.is_file() else None


def _read_env_file(env_name: str) -> str | None:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return None
    try:
        return Path(raw).read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _cookie_header_from_storage_state(path: str, domain_hint: str) -> str | None:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    cookies = payload.get("cookies") if isinstance(payload, dict) else None
    if not isinstance(cookies, list):
        return None

    parts: list[str] = []
    for cookie in cookies:
        if not isinstance(cookie, dict) or not _cookie_matches(cookie, domain_hint):
            continue
        name = _clean_cookie_piece(cookie.get("name"))
        value = _clean_cookie_piece(cookie.get("value"))
        if name and value is not None:
            parts.append(f"{name}={value}")
    return "; ".join(parts) or None


def _cookie_matches(cookie: dict[str, Any], domain_hint: str) -> bool:
    domain = _clean_cookie_piece(cookie.get("domain")) or ""
    if not domain:
        return False
    normalized_domain = domain.lower().lstrip(".")
    normalized_hint = domain_hint.lower().lstrip(".")
    return normalized_domain == normalized_hint or normalized_domain.endswith(f".{normalized_hint}")


def _clean_cookie_piece(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).replace("\r", "").replace("\n", "").strip()
