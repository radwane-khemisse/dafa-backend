"""admin analytics and geo validation

Revision ID: 202605080001
Revises: 202604300001
Create Date: 2026-05-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605080001"
down_revision: Union[str, None] = "202604300001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("ip_country_code", sa.String(length=2), nullable=True))
    op.add_column("orders", sa.Column("ip_city", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("ip_is_vpn", sa.Boolean(), nullable=True))
    op.add_column("orders", sa.Column("ip_is_valid_ksa", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("orders", sa.Column("ip_validation_reason", sa.String(length=255), nullable=True))

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_name", sa.String(length=80), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("product_id", sa.String(length=80), nullable=True),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("ip_country_code", sa.String(length=2), nullable=True),
        sa.Column("ip_city", sa.String(length=120), nullable=True),
        sa.Column("ip_is_vpn", sa.Boolean(), nullable=True),
        sa.Column("ip_is_valid_ksa", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ip_validation_reason", sa.String(length=255), nullable=True),
        sa.Column("utm_source", sa.String(length=255), nullable=True),
        sa.Column("utm_medium", sa.String(length=255), nullable=True),
        sa.Column("utm_campaign", sa.String(length=255), nullable=True),
        sa.Column("utm_content", sa.String(length=255), nullable=True),
        sa.Column("utm_term", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analytics_events_created_at", "analytics_events", ["created_at"])
    op.create_index("ix_analytics_events_event_id", "analytics_events", ["event_id"])
    op.create_index("ix_analytics_events_event_name", "analytics_events", ["event_name"])
    op.create_index("ix_analytics_events_ip_country_code", "analytics_events", ["ip_country_code"])
    op.create_index("ix_analytics_events_ip_is_valid_ksa", "analytics_events", ["ip_is_valid_ksa"])
    op.create_index("ix_analytics_events_product_id", "analytics_events", ["product_id"])
    op.create_index("ix_analytics_events_session_id", "analytics_events", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_analytics_events_session_id", table_name="analytics_events")
    op.drop_index("ix_analytics_events_product_id", table_name="analytics_events")
    op.drop_index("ix_analytics_events_ip_is_valid_ksa", table_name="analytics_events")
    op.drop_index("ix_analytics_events_ip_country_code", table_name="analytics_events")
    op.drop_index("ix_analytics_events_event_name", table_name="analytics_events")
    op.drop_index("ix_analytics_events_event_id", table_name="analytics_events")
    op.drop_index("ix_analytics_events_created_at", table_name="analytics_events")
    op.drop_table("analytics_events")
    op.drop_column("orders", "ip_validation_reason")
    op.drop_column("orders", "ip_is_valid_ksa")
    op.drop_column("orders", "ip_is_vpn")
    op.drop_column("orders", "ip_city")
    op.drop_column("orders", "ip_country_code")
