"""offer market prices

Revision ID: 202605210003
Revises: 202605210002
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605210003"
down_revision: str | None = "202605210002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "offer_market_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(length=80), nullable=False),
        sa.Column("offer_id", sa.String(length=40), nullable=False),
        sa.Column("market_code", sa.String(length=10), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "offer_id", "market_code", name="uq_offer_market_price"),
    )
    op.create_index(op.f("ix_offer_market_prices_product_id"), "offer_market_prices", ["product_id"], unique=False)
    op.create_index(op.f("ix_offer_market_prices_offer_id"), "offer_market_prices", ["offer_id"], unique=False)
    op.create_index(op.f("ix_offer_market_prices_market_code"), "offer_market_prices", ["market_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_offer_market_prices_market_code"), table_name="offer_market_prices")
    op.drop_index(op.f("ix_offer_market_prices_offer_id"), table_name="offer_market_prices")
    op.drop_index(op.f("ix_offer_market_prices_product_id"), table_name="offer_market_prices")
    op.drop_table("offer_market_prices")
