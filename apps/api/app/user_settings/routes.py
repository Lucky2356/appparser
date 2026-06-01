from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import User
from app.notifications.delivery import deliver_telegram_notification
from app.user_settings.schemas import TestTelegramResponse, UserSettingsRead, UserSettingsUpdate


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=UserSettingsRead)
def get_settings(user: User = Depends(get_current_user)) -> User:
    return user


@router.put("", response_model=UserSettingsRead)
def update_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    chat_id = payload.telegram_chat_id.strip() if payload.telegram_chat_id else None
    user.telegram_chat_id = chat_id
    user.telegram_notifications_enabled = bool(chat_id and payload.telegram_notifications_enabled)
    db.commit()
    db.refresh(user)
    return user


@router.post("/test-telegram", response_model=TestTelegramResponse)
def test_telegram(user: User = Depends(get_current_user)) -> TestTelegramResponse:
    sent = deliver_telegram_notification(user, "Appsparcer: тестовое уведомление")
    if sent:
        return TestTelegramResponse(sent=True, message="Тестовое уведомление отправлено")
    return TestTelegramResponse(
        sent=False,
        message="Не удалось отправить уведомление. Проверьте bot token, chat ID и включение Telegram-уведомлений.",
    )
