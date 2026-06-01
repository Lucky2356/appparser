"""tracked product identity

Revision ID: 20260601_0004
Revises: 20260601_0003
Create Date: 2026-06-01 03:00:00 UTC
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0004"
down_revision = "20260601_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracked_products", sa.Column("external_id", sa.String(length=160), nullable=True))
    op.add_column("tracked_products", sa.Column("image_url", sa.Text(), nullable=True))
    op.create_index("ix_tracked_products_external_id", "tracked_products", ["external_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tracked_products_external_id", table_name="tracked_products")
    op.drop_column("tracked_products", "image_url")
    op.drop_column("tracked_products", "external_id")
