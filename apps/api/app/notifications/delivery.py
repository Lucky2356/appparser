from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings
from app.models import User


def deliver_telegram_notification(user: User, text: str) -> bool:
    if not settings.telegram_bot_token:
        return False
    if not user.telegram_notifications_enabled or not user.telegram_chat_id:
        return False

    payload = urlencode(
        {
            "chat_id": user.telegram_chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.telegram_timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
            return bool(body.get("ok"))
    except Exception:
        return False
