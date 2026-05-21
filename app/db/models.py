from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_order_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    phone_e164: Mapped[str] = mapped_column(String(32), index=True)
    phone_digits: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending_confirmation")

    subtotal: Mapped[int] = mapped_column(Integer)
    delivery_fee: Mapped[int] = mapped_column(Integer, default=0)
    discount: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(20), default="ريال")
    market_code: Mapped[str] = mapped_column(String(10), default="ksa", index=True)
    payment_method: Mapped[str] = mapped_column(String(20), default="COD")

    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    ip_city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    ip_is_vpn: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ip_is_valid_ksa: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_validation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fbp: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fbc: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ttp: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ttclid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sc_click_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_content: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_term: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    upsell_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    sheet_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    capi_meta_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    capi_tiktok_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    capi_snap_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(String(80))
    title_ar: Mapped[str] = mapped_column(String(255))
    offer_id: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    total_price: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=True)
    platform: Mapped[str] = mapped_column(String(40))
    event_name: Mapped[str] = mapped_column(String(80))
    event_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40))
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_name: Mapped[str] = mapped_column(String(80), index=True)
    event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    market_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, index=True)
    ip_city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    ip_is_vpn: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ip_is_valid_ksa: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    ip_validation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_content: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_term: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class CatalogVisibility(Base):
    __tablename__ = "catalog_visibility"
    __table_args__ = (UniqueConstraint("item_type", "item_id", name="uq_catalog_visibility_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarketStore(Base):
    __tablename__ = "market_stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    country_name_ar: Mapped[str] = mapped_column(String(80), nullable=False)
    country_name_en: Mapped[str] = mapped_column(String(80), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    currency: Mapped[str] = mapped_column(String(20), nullable=False, default="ريال")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CatalogMarketVisibility(Base):
    __tablename__ = "catalog_market_visibility"
    __table_args__ = (UniqueConstraint("item_type", "item_id", "market_code", name="uq_catalog_market_visibility_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    market_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
