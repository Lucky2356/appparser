"""initial schema

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01 00:00:00 UTC
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "searches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("marketplaces", sa.JSON(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("sort", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_searches_status", "searches", ["status"], unique=False)
    op.create_index("ix_searches_user_id", "searches", ["user_id"], unique=False)

    op.create_table(
        "tracked_products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("marketplace", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("last_price", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tracked_products_user_id", "tracked_products", ["user_id"], unique=False)

    op.create_table(
        "offers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("search_id", sa.String(length=36), nullable=False),
        sa.Column("external_id", sa.String(length=160), nullable=False),
        sa.Column("marketplace", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("old_price", sa.Float(), nullable=True),
        sa.Column("discount_percent", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        sa.Column("seller_name", sa.String(length=255), nullable=True),
        sa.Column("seller_rating", sa.Float(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("availability", sa.Boolean(), nullable=False),
        sa.Column("delivery_info", sa.String(length=255), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("score_reasons", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["search_id"], ["searches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offers_external_id", "offers", ["external_id"], unique=False)
    op.create_index("ix_offers_marketplace", "offers", ["marketplace"], unique=False)
    op.create_index("ix_offers_search_id", "offers", ["search_id"], unique=False)

    op.create_table(
        "favorites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("offer_id", sa.String(length=36), nullable=True),
        sa.Column("marketplace", sa.String(length=60), nullable=False),
        sa.Column("external_id", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_favorites_offer_id", "favorites", ["offer_id"], unique=False)
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"], unique=False)

    op.create_table(
        "parser_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("search_id", sa.String(length=36), nullable=False),
        sa.Column("marketplace", sa.String(length=60), nullable=False),
        sa.Column("level", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["search_id"], ["searches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parser_logs_search_id", "parser_logs", ["search_id"], unique=False)

    op.create_table(
        "price_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tracked_product_id", sa.String(length=36), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tracked_product_id"], ["tracked_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_history_tracked_product_id", "price_history", ["tracked_product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_price_history_tracked_product_id", table_name="price_history")
    op.drop_table("price_history")
    op.drop_index("ix_parser_logs_search_id", table_name="parser_logs")
    op.drop_table("parser_logs")
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_index("ix_favorites_offer_id", table_name="favorites")
    op.drop_table("favorites")
    op.drop_index("ix_offers_search_id", table_name="offers")
    op.drop_index("ix_offers_marketplace", table_name="offers")
    op.drop_index("ix_offers_external_id", table_name="offers")
    op.drop_table("offers")
    op.drop_index("ix_tracked_products_user_id", table_name="tracked_products")
    op.drop_table("tracked_products")
    op.drop_index("ix_searches_user_id", table_name="searches")
    op.drop_index("ix_searches_status", table_name="searches")
    op.drop_table("searches")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
