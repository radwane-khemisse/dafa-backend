from typing import Any

from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    event_name: str = Field(min_length=2, max_length=80)
    event_id: str | None = Field(default=None, max_length=255)
    session_id: str | None = Field(default=None, max_length=255)
    product_id: str | None = Field(default=None, max_length=80)
    path: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    utm_source: str | None = Field(default=None, max_length=255)
    utm_medium: str | None = Field(default=None, max_length=255)
    utm_campaign: str | None = Field(default=None, max_length=255)
    utm_content: str | None = Field(default=None, max_length=255)
    utm_term: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] | None = None


class AnalyticsEventResponse(BaseModel):
    ok: bool
    counted: bool

