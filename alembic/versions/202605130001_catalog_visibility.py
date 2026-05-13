"""catalog visibility controls

Revision ID: 202605130001
Revises: 202605100001
Create Date: 2026-05-13 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605130001"
down_revision: str | None = "202605100001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "catalog_visibility",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_id", sa.String(length=80), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("item_type", "item_id", name="uq_catalog_visibility_item"),
    )
    op.create_index("ix_catalog_visibility_hidden", "catalog_visibility", ["hidden"])
    op.create_index("ix_catalog_visibility_item_id", "catalog_visibility", ["item_id"])
    op.create_index("ix_catalog_visibility_item_type", "catalog_visibility", ["item_type"])


def downgrade() -> None:
    op.drop_index("ix_catalog_visibility_item_type", table_name="catalog_visibility")
    op.drop_index("ix_catalog_visibility_item_id", table_name="catalog_visibility")
    op.drop_index("ix_catalog_visibility_hidden", table_name="catalog_visibility")
    op.drop_table("catalog_visibility")
