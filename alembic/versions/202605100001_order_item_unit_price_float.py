"""store order item unit prices as decimals

Revision ID: 202605100001
Revises: 202605080001
Create Date: 2026-05-10 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605100001"
down_revision: str | None = "202605080001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "order_items",
        "unit_price",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "order_items",
        "unit_price",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
