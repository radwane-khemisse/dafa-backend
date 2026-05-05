"""initial order schema

Revision ID: 202604300001
Revises:
Create Date: 2026-04-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202604300001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_order_id", sa.String(length=40), nullable=False, unique=True, index=True),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("phone_e164", sa.String(length=32), nullable=False, index=True),
        sa.Column("phone_digits", sa.String(length=32), nullable=False, index=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending_confirmation"),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("delivery_fee", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="SAR"),
        sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="COD"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("fbp", sa.String(length=255), nullable=True),
        sa.Column("fbc", sa.String(length=255), nullable=True),
        sa.Column("ttp", sa.String(length=255), nullable=True),
        sa.Column("ttclid", sa.String(length=255), nullable=True),
        sa.Column("sc_click_id", sa.String(length=255), nullable=True),
        sa.Column("utm_source", sa.String(length=255), nullable=True),
        sa.Column("utm_medium", sa.String(length=255), nullable=True),
        sa.Column("utm_campaign", sa.String(length=255), nullable=True),
        sa.Column("utm_content", sa.String(length=255), nullable=True),
        sa.Column("utm_term", sa.String(length=255), nullable=True),
        sa.Column("event_id", sa.String(length=255), nullable=False, index=True),
        sa.Column("upsell_accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sheet_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capi_meta_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capi_tiktok_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capi_snap_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("product_id", sa.String(length=80), nullable=False),
        sa.Column("title_ar", sa.String(length=255), nullable=False),
        sa.Column("offer_id", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Integer(), nullable=False),
    )

    op.create_table(
        "tracking_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("event_name", sa.String(length=80), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("tracking_events")
    op.drop_table("order_items")
    op.drop_table("orders")

