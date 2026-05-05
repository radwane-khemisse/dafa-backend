import time

import httpx

from app.core.config import Settings
from app.services.hashing import sha256_hex


def send_tiktok_purchase(payload: dict, settings: Settings) -> tuple[bool, int | None, str | None]:
    if not settings.enable_capi or not settings.tiktok_pixel_code or not settings.tiktok_access_token:
        return False, None, "TikTok Events API disabled or missing credentials."

    phone_source = payload["phone_e164"] if settings.tiktok_phone_hash_mode == "e164" else payload["phone_digits"]
    user = {
        "phone": sha256_hex(phone_source),
        "ip": payload.get("ip_address"),
        "user_agent": payload.get("user_agent"),
        "ttp": payload.get("ttp"),
        "ttclid": payload.get("ttclid"),
    }
    user = {key: value for key, value in user.items() if value}

    event = {
        "event": "Purchase",
        "event_id": payload["event_id"],
        "event_time": int(time.time()),
        "event_source": "web",
        "event_source_url": payload.get("source_url"),
        "user": user,
        "properties": {
            "currency": "SAR",
            "value": payload["total"],
            "content_type": "product",
            "contents": [
                {
                    "content_id": item["product_id"],
                    "content_name": item["title_ar"],
                    "quantity": item["quantity"],
                    "price": item["total_price"],
                }
                for item in payload["items"]
            ],
        },
    }
    if settings.tiktok_test_event_code:
        event["test_event_code"] = settings.tiktok_test_event_code

    body = {
        "pixel_code": settings.tiktok_pixel_code,
        "event": event["event"],
        "event_id": event["event_id"],
        "timestamp": event["event_time"],
        "context": {
            "page": {"url": event.get("event_source_url")},
            "user": user,
        },
        "properties": event["properties"],
    }

    try:
        with httpx.Client(timeout=8) as client:
            response = client.post(
                settings.tiktok_events_api_url,
                headers={"Access-Token": settings.tiktok_access_token},
                json=body,
            )
        return response.is_success, response.status_code, response.text[:1000]
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)

