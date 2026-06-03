"""mini portable blender catalog defaults

Revision ID: 202605210007
Revises: 202605210006
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605210007"
down_revision: str | None = "202605210006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PRODUCT_ID = "mini_portable_blender"
SKU = "MP-CUQRQUGWOOXD"
KSA_MARKET = "ksa"
RIYADH_WAREHOUSE = "COD NETWORK - Riyadh Warehouse KSA"
MARKETS = ("bhr", "ksa", "kwt", "omn", "qat", "uae")


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO product_market_details (product_id, market_code, sku, cost, warehouse)
            VALUES (:product_id, :market_code, :sku, 0, :warehouse)
            ON CONFLICT (product_id, market_code)
            DO UPDATE SET sku = EXCLUDED.sku, warehouse = EXCLUDED.warehouse
            """
        ).bindparams(
            product_id=PRODUCT_ID,
            market_code=KSA_MARKET,
            sku=SKU,
            warehouse=RIYADH_WAREHOUSE,
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO product_market_details (product_id, market_code, sku, cost, warehouse)
            VALUES ('vegetable_cutter', :market_code, 'DAFA-VC-4821', 0, :warehouse)
            ON CONFLICT (product_id, market_code)
            DO UPDATE SET warehouse = EXCLUDED.warehouse
            """
        ).bindparams(market_code=KSA_MARKET, warehouse=RIYADH_WAREHOUSE)
    )
    for market_code in MARKETS:
        op.execute(
            sa.text(
                """
                INSERT INTO catalog_market_visibility (item_type, item_id, market_code, visible)
                VALUES ('product', :product_id, :market_code, :visible)
                ON CONFLICT (item_type, item_id, market_code)
                DO UPDATE SET visible = EXCLUDED.visible
                """
            ).bindparams(
                product_id=PRODUCT_ID,
                market_code=market_code,
                visible=market_code == KSA_MARKET,
            )
        )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM catalog_market_visibility WHERE item_type = 'product' AND item_id = :product_id").bindparams(
            product_id=PRODUCT_ID
        )
    )
    op.execute(sa.text("DELETE FROM product_market_details WHERE product_id = :product_id").bindparams(product_id=PRODUCT_ID))
