"""pack market prices

Revision ID: 202605210004
Revises: 202605210003
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605210004"
down_revision: str | None = "202605210003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pack_market_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pack_id", sa.String(length=80), nullable=False),
        sa.Column("market_code", sa.String(length=10), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pack_id", "market_code", name="uq_pack_market_price"),
    )
    op.create_index(op.f("ix_pack_market_prices_pack_id"), "pack_market_prices", ["pack_id"], unique=False)
    op.create_index(op.f("ix_pack_market_prices_market_code"), "pack_market_prices", ["market_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pack_market_prices_market_code"), table_name="pack_market_prices")
    op.drop_index(op.f("ix_pack_market_prices_pack_id"), table_name="pack_market_prices")
    op.drop_table("pack_market_prices")
