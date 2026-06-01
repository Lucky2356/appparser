"""notifications and tracking checks

Revision ID: 20260601_0002
Revises: 20260601_0001
Create Date: 2026-06-01 01:00:00 UTC
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0002"
down_revision = "20260601_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracked_products", sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tracked_products", sa.Column("last_notified_price", sa.Float(), nullable=True))

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_entity_id", "notifications", ["entity_id"], unique=False)
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_entity_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("tracked_products", "last_notified_price")
    op.drop_column("tracked_products", "last_checked_at")
