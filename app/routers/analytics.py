import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AnalyticsEvent
from app.db.session import get_db
from app.schemas.analytics import AnalyticsEventCreate, AnalyticsEventResponse
from app.services.ip_quality import client_ip_from_request, validate_ip

router = APIRouter(prefix="/events", tags=["analytics"])


@router.post("", response_model=AnalyticsEventResponse)
def create_analytics_event(
    payload: AnalyticsEventCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> AnalyticsEventResponse:
    settings = get_settings()
    ip_validation = validate_ip(client_ip_from_request(request), settings)
    event = AnalyticsEvent(
        event_name=payload.event_name,
        event_id=payload.event_id,
        session_id=payload.session_id,
        product_id=payload.product_id,
        path=payload.path,
        referrer=payload.referrer,
        user_agent=payload.user_agent or request.headers.get("user-agent"),
        ip_address=ip_validation.ip_address,
        ip_country_code=ip_validation.country_code,
        ip_city=ip_validation.city,
        ip_is_vpn=ip_validation.is_vpn,
        ip_is_valid_ksa=ip_validation.is_valid_ksa,
        ip_validation_reason=ip_validation.reason,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        utm_content=payload.utm_content,
        utm_term=payload.utm_term,
        metadata_json=json.dumps(payload.metadata, ensure_ascii=True) if payload.metadata else None,
    )
    db.add(event)
    db.commit()
    return AnalyticsEventResponse(ok=True, counted=event.ip_is_valid_ksa)
