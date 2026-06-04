"""product upsell controls

Revision ID: 202605210009
Revises: 202605210008
Create Date: 2026-06-04 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "202605210009"
down_revision: Union[str, None] = "202605210008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_upsells",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_product_id", sa.String(length=80), nullable=False),
        sa.Column("target_product_id", sa.String(length=80), nullable=False),
        sa.Column("market_code", sa.String(length=10), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_product_id", "target_product_id", "market_code", name="uq_product_upsell"),
    )
    op.create_index("ix_product_upsells_source_product_id", "product_upsells", ["source_product_id"])
    op.create_index("ix_product_upsells_target_product_id", "product_upsells", ["target_product_id"])
    op.create_index("ix_product_upsells_market_code", "product_upsells", ["market_code"])


def downgrade() -> None:
    op.drop_index("ix_product_upsells_market_code", table_name="product_upsells")
    op.drop_index("ix_product_upsells_target_product_id", table_name="product_upsells")
    op.drop_index("ix_product_upsells_source_product_id", table_name="product_upsells")
    op.drop_table("product_upsells")
