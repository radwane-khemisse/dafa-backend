"""catalog market sku and cost details

Revision ID: 202605210005
Revises: 202605210004
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605210005"
down_revision: str | None = "202605210004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_market_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(length=80), nullable=False),
        sa.Column("market_code", sa.String(length=10), nullable=False),
        sa.Column("sku", sa.String(length=120), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "market_code", name="uq_product_market_detail"),
    )
    op.create_index(op.f("ix_product_market_details_product_id"), "product_market_details", ["product_id"], unique=False)
    op.create_index(op.f("ix_product_market_details_market_code"), "product_market_details", ["market_code"], unique=False)

    op.create_table(
        "pack_market_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pack_id", sa.String(length=80), nullable=False),
        sa.Column("market_code", sa.String(length=10), nullable=False),
        sa.Column("sku", sa.String(length=120), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pack_id", "market_code", name="uq_pack_market_detail"),
    )
    op.create_index(op.f("ix_pack_market_details_pack_id"), "pack_market_details", ["pack_id"], unique=False)
    op.create_index(op.f("ix_pack_market_details_market_code"), "pack_market_details", ["market_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pack_market_details_market_code"), table_name="pack_market_details")
    op.drop_index(op.f("ix_pack_market_details_pack_id"), table_name="pack_market_details")
    op.drop_table("pack_market_details")
    op.drop_index(op.f("ix_product_market_details_market_code"), table_name="product_market_details")
    op.drop_index(op.f("ix_product_market_details_product_id"), table_name="product_market_details")
    op.drop_table("product_market_details")
