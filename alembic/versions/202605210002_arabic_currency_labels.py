"""arabic currency labels

Revision ID: 202605210002
Revises: 202605210001
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605210002"
down_revision: str | None = "202605210001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("orders", "currency", type_=sa.String(length=20), existing_type=sa.String(length=3), server_default="ريال")
    op.alter_column("market_stores", "currency", type_=sa.String(length=20), existing_type=sa.String(length=3))

    market_stores = sa.table(
        "market_stores",
        sa.column("market_code", sa.String),
        sa.column("currency", sa.String),
    )
    op.execute(market_stores.update().where(market_stores.c.market_code == "ksa").values(currency="ريال"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "kwt").values(currency="دينار"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "uae").values(currency="درهم"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "qat").values(currency="ريال"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "bhr").values(currency="دينار"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "omn").values(currency="ريال"))


def downgrade() -> None:
    market_stores = sa.table(
        "market_stores",
        sa.column("market_code", sa.String),
        sa.column("currency", sa.String),
    )
    op.execute(market_stores.update().where(market_stores.c.market_code == "ksa").values(currency="SAR"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "kwt").values(currency="KWD"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "uae").values(currency="AED"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "qat").values(currency="QAR"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "bhr").values(currency="BHD"))
    op.execute(market_stores.update().where(market_stores.c.market_code == "omn").values(currency="OMR"))
    op.alter_column("market_stores", "currency", type_=sa.String(length=3), existing_type=sa.String(length=20))
    op.alter_column("orders", "currency", type_=sa.String(length=3), existing_type=sa.String(length=20), server_default="SAR")
