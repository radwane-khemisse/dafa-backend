"""product market warehouses

Revision ID: 202605210006
Revises: 202605210005
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605210006"
down_revision: str | None = "202605210005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


DEFAULT_WAREHOUSES = {
    "kwt": "COD NETWORK - Kuwait Warehouse KWT",
    "ksa": "COD NETWORK - RUH 2 Warehouse KSA",
    "uae": "COD NETWORK - Dubai Warehouse UAE",
    "qat": "COD NETWORK - Qatar Warehouse QAT",
    "bhr": "COD NETWORK - Bahrain Warehouse",
    "omn": "COD Network Oman 1",
}


def upgrade() -> None:
    op.add_column("product_market_details", sa.Column("warehouse", sa.String(length=160), nullable=False, server_default=""))
    details = sa.table(
        "product_market_details",
        sa.column("market_code", sa.String),
        sa.column("warehouse", sa.String),
    )
    for market_code, warehouse in DEFAULT_WAREHOUSES.items():
        op.execute(details.update().where(details.c.market_code == market_code).values(warehouse=warehouse))


def downgrade() -> None:
    op.drop_column("product_market_details", "warehouse")
