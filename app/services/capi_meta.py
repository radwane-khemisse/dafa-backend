import time

import httpx

from app.core.config import Settings
from app.services.hashing import sha256_hex


def send_meta_purchase(payload: dict, settings: Settings) -> tuple[bool, int | None, str | None]:
    if not settings.enable_capi or not settings.meta_pixel_id or not settings.meta_access_token:
        return False, None, "Meta CAPI disabled or missing credentials."

    url = (
        f"https://graph.facebook.com/{settings.meta_graph_version}/"
        f"{settings.meta_pixel_id}/events"
    )
    user_data = {
        "ph": [sha256_hex(payload["phone_digits"])],
        "client_ip_address": payload.get("ip_address"),
        "client_user_agent": payload.get("user_agent"),
        "fbp": payload.get("fbp"),
        "fbc": payload.get("fbc"),
    }
    user_data = {key: value for key, value in user_data.items() if value}

    data = {
        "data": [
            {
                "event_name": "Purchase",
                "event_time": int(time.time()),
                "event_id": payload["event_id"],
                "action_source": "website",
                "event_source_url": payload.get("source_url") or settings.frontend_url,
                "user_data": user_data,
                "custom_data": {
                    "currency": "SAR",
                    "value": payload["total"],
                    "content_ids": [item["product_id"] for item in payload["items"]],
                    "contents": [
                        {
                            "id": item["product_id"],
                            "quantity": item["quantity"],
                            "item_price": item["total_price"],
                        }
                        for item in payload["items"]
                    ],
                    "num_items": sum(item["quantity"] for item in payload["items"]),
                },
            }
        ],
        "access_token": settings.meta_access_token,
    }
    if settings.meta_test_event_code:
        data["test_event_code"] = settings.meta_test_event_code

    try:
        with httpx.Client(timeout=8) as client:
            response = client.post(url, json=data)
        return response.is_success, response.status_code, response.text[:1000]
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)

