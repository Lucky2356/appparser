from datetime import datetime

from app.schemas import CamelModel


class NotificationRead(CamelModel):
    id: str
    type: str
    title: str
    message: str
    entity_id: str | None = None
    is_read: bool
    created_at: datetime


class UnreadCount(CamelModel):
    count: int
