from typing import Any

from pydantic import BaseModel, Field


class TrackingClientIn(BaseModel):
    source_url: str | None = None
    landing_page: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    ip: str | None = None
    fbp: str | None = None
    fbc: str | None = None
    fbclid: str | None = None
    ttp: str | None = None
    ttclid: str | None = None
    sc_click_id: str | None = None
    sc_cookie1: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None


class TrackingItemIn(BaseModel):
    product_id: str
    title_ar: str | None = None
    quantity: int = 1
    unit_price: float | None = None
    total_price: int | None = None


class TrackingEventCreate(BaseModel):
    event_name: str = Field(min_length=2, max_length=80)
    event_id: str = Field(min_length=8, max_length=255)
    session_id: str | None = Field(default=None, max_length=255)
    product_id: str | None = Field(default=None, max_length=80)
    content_name: str | None = None
    content_ids: list[str] = Field(default_factory=list)
    items: list[TrackingItemIn] = Field(default_factory=list)
    value: int | float | None = None
    currency: str = "ريال"
    name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    metadata: dict[str, Any] | None = None
    client: TrackingClientIn = Field(default_factory=TrackingClientIn)


class TrackingEventResponse(BaseModel):
    ok: bool
    counted: bool
