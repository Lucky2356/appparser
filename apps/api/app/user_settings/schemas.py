from pydantic import Field

from app.schemas import CamelModel


class UserSettingsRead(CamelModel):
    email: str
    telegram_chat_id: str | None = None
    telegram_notifications_enabled: bool = False


class UserSettingsUpdate(CamelModel):
    telegram_chat_id: str | None = Field(default=None, max_length=80)
    telegram_notifications_enabled: bool = False
