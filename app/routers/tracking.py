import json

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AnalyticsEvent, TrackingEvent
from app.db.session import SessionLocal, get_db
from app.schemas.tracking import TrackingEventCreate, TrackingEventResponse
from app.services.ip_quality import client_ip_from_request, validate_ip
from app.services.markets import valid_market_codes
from app.services.phone import PhoneValidationError, normalize_gulf_phone
from app.services.tracking import META_EVENTS, event_time_seconds, send_all_platform_events
from urllib.parse import urlparse

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.post("/events", response_model=TrackingEventResponse)
def create_tracking_event(
    payload: TrackingEventCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TrackingEventResponse:
    settings = get_settings()
    client_ip = payload.client.ip or client_ip_from_request(request)
    ip_validation = validate_ip(client_ip, settings)
    user_agent = payload.client.user_agent or request.headers.get("user-agent")
    source_url = payload.client.source_url or payload.client.landing_page or settings.frontend_url
    market_code = _market_code_from_url(source_url)

    analytics_event = AnalyticsEvent(
        event_name=payload.event_name,
        event_id=payload.event_id,
        session_id=payload.session_id,
        product_id=payload.product_id or (payload.content_ids[0] if payload.content_ids else None),
        market_code=market_code,
        path=source_url,
        referrer=payload.client.referrer,
        user_agent=user_agent,
        ip_address=ip_validation.ip_address,
        ip_country_code=ip_validation.country_code,
        ip_city=ip_validation.city,
        ip_is_vpn=ip_validation.is_vpn,
        ip_is_valid_ksa=ip_validation.is_valid_ksa,
        ip_validation_reason=ip_validation.reason,
        utm_source=payload.client.utm_source,
        utm_medium=payload.client.utm_medium,
        utm_campaign=payload.client.utm_campaign,
        utm_content=payload.client.utm_content,
        utm_term=payload.client.utm_term,
        metadata_json=json.dumps(payload.metadata, ensure_ascii=True) if payload.metadata else None,
    )
    db.add(analytics_event)
    db.commit()

    phone_e164 = None
    phone_digits = None
    if payload.phone:
        try:
            phone_e164, phone_digits = normalize_gulf_phone(payload.phone, market_code)
        except PhoneValidationError:
            phone_e164 = None
            phone_digits = None

    tracking_event = {
        "event_name": payload.event_name,
        "event_id": payload.event_id,
        "event_time": event_time_seconds(),
        "source_url": source_url,
        "referrer": payload.client.referrer,
        "user_agent": user_agent,
        "ip_address": ip_validation.ip_address,
        "customer_name": payload.name,
        "phone_e164": phone_e164,
        "phone_digits": phone_digits,
        "value": payload.value,
        "currency": payload.currency,
        "items": [item.model_dump() for item in payload.items],
        "product_id": payload.product_id,
        "content_name": payload.content_name,
        "content_ids": payload.content_ids,
        "metadata": payload.metadata,
        "fbp": payload.client.fbp,
        "fbc": payload.client.fbc,
        "fbclid": payload.client.fbclid,
        "ttp": payload.client.ttp,
        "ttclid": payload.client.ttclid,
        "sc_click_id": payload.client.sc_click_id,
        "sc_cookie1": payload.client.sc_cookie1,
    }
    if payload.event_name in META_EVENTS:
        background_tasks.add_task(send_and_log_tracking_event, tracking_event)
    return TrackingEventResponse(ok=True, counted=analytics_event.ip_is_valid_ksa)


def _market_code_from_url(source_url: str | None) -> str:
    path = urlparse(source_url or "").path
    segment = path.strip("/").split("/", 1)[0].lower()
    return segment if segment in valid_market_codes() else "ksa"


def send_and_log_tracking_event(event: dict) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        for platform, platform_event_name, ok, response_status, response_body in send_all_platform_events(event, settings):
            db.add(
                TrackingEvent(
                    order_id=None,
                    platform=platform,
                    event_name=platform_event_name,
                    event_id=event["event_id"],
                    status="sent" if ok else "skipped_or_failed",
                    response_status=response_status,
                    response_body=response_body,
                )
            )
        db.commit()
    finally:
        db.close()
