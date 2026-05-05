import time

import httpx

from app.core.config import Settings
from app.services.hashing import sha256_hex


def send_snap_purchase(payload: dict, settings: Settings) -> tuple[bool, int | None, str | None]:
    if not settings.enable_capi or not settings.snap_pixel_id or not settings.snap_access_token:
        return False, None, "Snap CAPI disabled or missing credentials."

    url = f"https://tr.snapchat.com/v3/{settings.snap_pixel_id}/events"
    body = {
        "data": [
            {
                "event_name": "PURCHASE",
                "event_time": int(time.time()),
                "event_id": payload["event_id"],
                "action_source": "WEB",
                "event_source_url": payload.get("source_url"),
                "user_data": {
                    "ph": sha256_hex(payload["phone_digits"]),
                    "client_ip_address": payload.get("ip_address"),
                    "client_user_agent": payload.get("user_agent"),
                },
                "custom_data": {
                    "currency": "SAR",
                    "value": payload["total"],
                    "content_ids": [item["product_id"] for item in payload["items"]],
                },
            }
        ]
    }

    try:
        with httpx.Client(timeout=8) as client:
            response = client.post(
                url,
                params={"access_token": settings.snap_access_token},
                json=body,
            )
        return response.is_success, response.status_code, response.text[:1000]
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)

