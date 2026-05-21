from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    product_id: str
    offer_id: str
    pack_id: str | None = None
    pack_name: str | None = None
    quantity: int | None = None
    unit_price: float | None = None
    total_price: int | None = None


class UpsellIn(BaseModel):
    accepted: bool = False
    product_id: str | None = None
    price: int | None = None


class TotalsIn(BaseModel):
    subtotal: int = 0
    delivery_fee: int = 0
    discount: int = 0
    total: int = 0
    currency: str = "ريال"


class ClientIn(BaseModel):
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


class OrderCreate(BaseModel):
    market_code: str = "ksa"
    event_id: str = Field(min_length=8)
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=32)
    items: list[OrderItemIn] = Field(min_length=1)
    upsell: UpsellIn | None = None
    totals: TotalsIn | None = None
    client: ClientIn = Field(default_factory=ClientIn)


class OrderCreateResponse(BaseModel):
    ok: bool
    order_id: str
    purchase_event_id: str
    status: str
