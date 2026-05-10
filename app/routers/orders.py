from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Order, OrderItem, TrackingEvent
from app.db.session import SessionLocal, get_db
from app.schemas.orders import OrderCreate, OrderCreateResponse
from app.services.capi_meta import send_meta_purchase
from app.services.capi_snap import send_snap_purchase
from app.services.capi_tiktok import send_tiktok_purchase
from app.services.catalog import calculate_items
from app.services.phone import PhoneValidationError, normalize_ksa_phone
from app.services.ip_quality import client_ip_from_request, validate_ip
from app.services.sheets import send_order_to_sheet
from app.services.tracking import purchase_event_id

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderCreateResponse)
def create_order(
    payload: OrderCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> OrderCreateResponse:
    try:
        phone_e164, phone_digits = normalize_ksa_phone(payload.phone)
        calculated_items = calculate_items(payload.items)
    except (PhoneValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    subtotal = sum(item["total_price"] for item in calculated_items)
    delivery_fee = 0
    discount = 0
    total = subtotal + delivery_fee - discount
    client_ip = payload.client.ip or client_ip_from_request(request)
    ip_validation = validate_ip(client_ip, get_settings())
    user_agent = payload.client.user_agent or request.headers.get("user-agent")

    order = Order(
        public_order_id="PENDING",
        customer_name=payload.name.strip(),
        phone_e164=phone_e164,
        phone_digits=phone_digits,
        status="pending_confirmation",
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount=discount,
        total=total,
        currency="SAR",
        payment_method="COD",
        source_url=payload.client.landing_page,
        referrer=payload.client.referrer,
        user_agent=user_agent,
        ip_address=ip_validation.ip_address,
        ip_country_code=ip_validation.country_code,
        ip_city=ip_validation.city,
        ip_is_vpn=ip_validation.is_vpn,
        ip_is_valid_ksa=ip_validation.is_valid_ksa,
        ip_validation_reason=ip_validation.reason,
        fbp=payload.client.fbp,
        fbc=payload.client.fbc,
        ttp=payload.client.ttp,
        ttclid=payload.client.ttclid,
        sc_click_id=payload.client.sc_click_id,
        utm_source=payload.client.utm_source,
        utm_medium=payload.client.utm_medium,
        utm_campaign=payload.client.utm_campaign,
        utm_content=payload.client.utm_content,
        utm_term=payload.client.utm_term,
        event_id="PENDING",
        upsell_accepted=bool(payload.upsell and payload.upsell.accepted),
    )
    db.add(order)
    db.flush()
    order.public_order_id = f"dafa-{datetime.now(UTC):%Y%m%d}-{order.id:04d}"
    order.event_id = purchase_event_id(order.public_order_id)

    for item in calculated_items:
        order_item = {key: value for key, value in item.items() if key != "sku"}
        db.add(OrderItem(order_id=order.id, **order_item))

    db.commit()
    db.refresh(order)

    integration_payload = _serialize_order(order, calculated_items, payload.client.model_dump())
    background_tasks.add_task(run_integrations, order.id, integration_payload)

    return OrderCreateResponse(ok=True, order_id=order.public_order_id, purchase_event_id=order.event_id, status=order.status)


def _serialize_order(order: Order, items: list[dict], client: dict | None = None) -> dict:
    created_at = order.created_at or datetime.now(UTC)
    client = client or {}
    return {
        "id": order.id,
        "public_order_id": order.public_order_id,
        "created_at": created_at.isoformat(),
        "customer_name": order.customer_name,
        "phone_e164": order.phone_e164,
        "phone_digits": order.phone_digits,
        "status": order.status,
        "items": items,
        "items_summary": "، ".join(f"{item['title_ar']} x{item['quantity']}" for item in items),
        "subtotal": order.subtotal,
        "discount": order.discount,
        "delivery_fee": order.delivery_fee,
        "total": order.total,
        "currency": order.currency,
        "payment_method": order.payment_method,
        "upsell_accepted": order.upsell_accepted,
        "source_url": order.source_url,
        "landing_page": order.source_url,
        "referrer": order.referrer,
        "user_agent": order.user_agent,
        "ip_address": order.ip_address,
        "fbp": order.fbp,
        "fbc": order.fbc,
        "fbclid": client.get("fbclid"),
        "ttp": order.ttp,
        "ttclid": order.ttclid,
        "sc_click_id": order.sc_click_id,
        "sc_cookie1": client.get("sc_cookie1"),
        "utm_source": order.utm_source,
        "utm_medium": order.utm_medium,
        "utm_campaign": order.utm_campaign,
        "utm_content": order.utm_content,
        "utm_term": order.utm_term,
        "event_id": order.event_id,
        "sheet_order": {
            "date": created_at.strftime("%d/%m/%Y"),
            "orderId": order.public_order_id,
            "country": "KSA",
            "name": order.customer_name,
            "phone": order.phone_digits,
            "product": "/".join(item["title_ar"] for item in items),
            "sku": "/".join(item["sku"] for item in items),
            "quantity": "/".join(str(item["quantity"]) for item in items),
            "totalprice": order.total,
            "currency": "SAR",
            "status": "",
        },
    }


def run_integrations(order_id: int, payload: dict) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        order = db.get(Order, order_id)
        if order is None:
            return

        sheet_ok, sheet_status, sheet_body = send_order_to_sheet(payload, settings)
        _log_tracking(db, order_id, "google_sheets", "OrderSync", payload["event_id"], sheet_ok, sheet_status, sheet_body)
        if sheet_ok:
            order.sheet_synced_at = datetime.now(UTC)

        meta_ok, meta_status, meta_body = send_meta_purchase(payload, settings)
        _log_tracking(db, order_id, "meta", "Purchase", payload["event_id"], meta_ok, meta_status, meta_body)
        if meta_ok:
            order.capi_meta_sent_at = datetime.now(UTC)

        tiktok_ok, tiktok_status, tiktok_body = send_tiktok_purchase(payload, settings)
        _log_tracking(db, order_id, "tiktok", "CompletePayment", payload["event_id"], tiktok_ok, tiktok_status, tiktok_body)
        if tiktok_ok:
            order.capi_tiktok_sent_at = datetime.now(UTC)

        snap_ok, snap_status, snap_body = send_snap_purchase(payload, settings)
        _log_tracking(db, order_id, "snapchat", "PURCHASE", payload["event_id"], snap_ok, snap_status, snap_body)
        if snap_ok:
            order.capi_snap_sent_at = datetime.now(UTC)

        db.commit()
    finally:
        db.close()


def _log_tracking(
    db: Session,
    order_id: int,
    platform: str,
    event_name: str,
    event_id: str,
    ok: bool,
    response_status: int | None,
    response_body: str | None,
) -> None:
    db.add(
        TrackingEvent(
            order_id=order_id,
            platform=platform,
            event_name=event_name,
            event_id=event_id,
            status="sent" if ok else "skipped_or_failed",
            response_status=response_status,
            response_body=response_body,
        )
    )
