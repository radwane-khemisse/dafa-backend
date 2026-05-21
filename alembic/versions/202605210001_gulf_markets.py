"""gulf market store controls

Revision ID: 202605210001
Revises: 202605130001
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605210001"
down_revision: str | None = "202605130001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("market_code", sa.String(length=10), nullable=False, server_default="ksa"))
    op.create_index("ix_orders_market_code", "orders", ["market_code"])
    op.add_column("analytics_events", sa.Column("market_code", sa.String(length=10), nullable=True))
    op.create_index("ix_analytics_events_market_code", "analytics_events", ["market_code"])

    op.create_table(
        "market_stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("market_code", sa.String(length=10), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("country_name_ar", sa.String(length=80), nullable=False),
        sa.Column("country_name_en", sa.String(length=80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("currency", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("market_code", name="uq_market_stores_market_code"),
    )
    op.create_index("ix_market_stores_active", "market_stores", ["active"])
    op.create_index("ix_market_stores_market_code", "market_stores", ["market_code"], unique=True)

    op.create_table(
        "catalog_market_visibility",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_id", sa.String(length=80), nullable=False),
        sa.Column("market_code", sa.String(length=10), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("item_type", "item_id", "market_code", name="uq_catalog_market_visibility_item"),
    )
    op.create_index("ix_catalog_market_visibility_item_id", "catalog_market_visibility", ["item_id"])
    op.create_index("ix_catalog_market_visibility_item_type", "catalog_market_visibility", ["item_type"])
    op.create_index("ix_catalog_market_visibility_market_code", "catalog_market_visibility", ["market_code"])
    op.create_index("ix_catalog_market_visibility_visible", "catalog_market_visibility", ["visible"])

    market_stores = sa.table(
        "market_stores",
        sa.column("market_code", sa.String),
        sa.column("country_code", sa.String),
        sa.column("country_name_ar", sa.String),
        sa.column("country_name_en", sa.String),
        sa.column("active", sa.Boolean),
        sa.column("currency", sa.String),
    )
    op.bulk_insert(
        market_stores,
        [
            {"market_code": "ksa", "country_code": "SA", "country_name_ar": "السعودية", "country_name_en": "Saudi Arabia", "active": True, "currency": "ريال"},
            {"market_code": "kwt", "country_code": "KW", "country_name_ar": "الكويت", "country_name_en": "Kuwait", "active": True, "currency": "دينار"},
            {"market_code": "uae", "country_code": "AE", "country_name_ar": "الإمارات", "country_name_en": "United Arab Emirates", "active": True, "currency": "درهم"},
            {"market_code": "qat", "country_code": "QA", "country_name_ar": "قطر", "country_name_en": "Qatar", "active": True, "currency": "ريال"},
            {"market_code": "bhr", "country_code": "BH", "country_name_ar": "البحرين", "country_name_en": "Bahrain", "active": True, "currency": "دينار"},
            {"market_code": "omn", "country_code": "OM", "country_name_ar": "عمان", "country_name_en": "Oman", "active": True, "currency": "ريال"},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_market_visibility_visible", table_name="catalog_market_visibility")
    op.drop_index("ix_catalog_market_visibility_market_code", table_name="catalog_market_visibility")
    op.drop_index("ix_catalog_market_visibility_item_type", table_name="catalog_market_visibility")
    op.drop_index("ix_catalog_market_visibility_item_id", table_name="catalog_market_visibility")
    op.drop_table("catalog_market_visibility")

    op.drop_index("ix_market_stores_market_code", table_name="market_stores")
    op.drop_index("ix_market_stores_active", table_name="market_stores")
    op.drop_table("market_stores")

    op.drop_index("ix_analytics_events_market_code", table_name="analytics_events")
    op.drop_column("analytics_events", "market_code")
    op.drop_index("ix_orders_market_code", table_name="orders")
    op.drop_column("orders", "market_code")
