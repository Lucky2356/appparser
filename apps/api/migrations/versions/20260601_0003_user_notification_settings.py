"""user notification settings

Revision ID: 20260601_0003
Revises: 20260601_0002
Create Date: 2026-06-01 02:00:00 UTC
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0003"
down_revision = "20260601_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.String(length=80), nullable=True))
    op.add_column(
        "users",
        sa.Column("telegram_notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "telegram_notifications_enabled")
    op.drop_column("users", "telegram_chat_id")
