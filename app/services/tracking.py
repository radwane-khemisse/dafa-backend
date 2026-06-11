from __future__ import annotations

import re
import time
import unicodedata
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.services.hashing import sha256_hex


CanonicalEvent = str

META_EVENTS: dict[CanonicalEvent, str] = {
    "PageView": "PageView",
    "ViewProduct": "ViewContent",
    "ViewContent": "ViewContent",
    "AddToCart": "AddToCart",
    "InitiateCheckout": "InitiateCheckout",
    "Lead": "Lead",
    "Purchase": "Purchase",
    "UpsellView": "UpsellView",
    "UpsellAccepted": "UpsellAccepted",
    "UpsellRejected": "UpsellRejected",
}

TIKTOK_EVENTS: dict[CanonicalEvent, str] = {
    "PageView": "PageView",
    "ViewProduct": "ViewContent",
    "ViewContent": "ViewContent",
    "AddToCart": "AddToCart",
    "InitiateCheckout": "InitiateCheckout",
    "Lead": "SubmitForm",
    "Purchase": "CompletePayment",
    "UpsellView": "UpsellView",
    "UpsellAccepted": "UpsellAccepted",
    "UpsellRejected": "UpsellRejected",
}

SNAP_EVENTS: dict[CanonicalEvent, str] = {
    "PageView": "PAGE_VIEW",
    "ViewProduct": "VIEW_CONTENT",
    "ViewContent": "VIEW_CONTENT",
    "AddToCart": "ADD_CART",
    "InitiateCheckout": "START_CHECKOUT",
    "Lead": "SIGN_UP",
    "Purchase": "PURCHASE",
    "UpsellView": "CUSTOM_EVENT_1",
    "UpsellAccepted": "CUSTOM_EVENT_2",
    "UpsellRejected": "CUSTOM_EVENT_3",
}

MARKET_CURRENCY_CODES = {
    "ksa": "SAR",
    "kwt": "KWD",
    "uae": "AED",
    "qat": "QAR",
    "bhr": "BHD",
    "omn": "OMR",
}


def purchase_event_id(order_id: str) -> str:
    return f"purchase_{order_id}"


def event_time_seconds() -> int:
    return int(time.time())


def event_time_milliseconds() -> int:
    return int(time.time() * 1000)


def normalize_phone_digits(value: str | None) -> str | None:
    digits = re.sub(r"\D+", "", value or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    return digits or None


def normalize_name(value: str | None) -> str | None:
    cleaned = " ".join((value or "").strip().lower().split())
    if not cleaned:
        return None
    normalized = "".join(
        char for char in cleaned if not unicodedata.category(char).startswith(("P", "S"))
    )
    compact = normalized.replace(" ", "")
    return compact or None


def normalize_currency_code(value: str | None, market_code: str | None = None) -> str:
    cleaned = (value or "").strip().upper()
    if re.fullmatch(r"[A-Z]{3}", cleaned):
        return cleaned
    return MARKET_CURRENCY_CODES.get((market_code or "").lower(), "SAR")


def hashed_name_parts(full_name: str | None) -> dict[str, str]:
    parts = [normalize_name(part) for part in (full_name or "").split()]
    parts = [part for part in parts if part]
    if not parts:
        return {}
    data = {"fn": sha256_hex(parts[0])}
    if len(parts) > 1:
        data["ln"] = sha256_hex(parts[-1])
    return data


def hashed_phone(phone_digits: str | None, phone_e164: str | None = None) -> str | None:
    normalized = normalize_phone_digits(phone_digits or phone_e164)
    return sha256_hex(normalized) if normalized else None


def normalize_phone_e164(value: str | None) -> str | None:
    digits = normalize_phone_digits(value)
    return f"+{digits}" if digits else None


def hash_tiktok_phone(phone_digits: str | None, phone_e164: str | None = None, mode: str = "e164") -> str | None:
    # TikTok requires SHA-256 for phone advanced matching. Keep the format
    # configurable because diagnostics can be sensitive to E.164 vs digits-only.
    if mode == "digits":
        normalized = normalize_phone_digits(phone_digits or phone_e164)
    else:
        normalized = normalize_phone_e164(phone_e164 or phone_digits)
    return sha256_hex(normalized) if normalized else None


def build_contents(items: list[dict[str, Any]] | None, content_ids: list[str] | None = None) -> list[dict[str, Any]]:
    if items:
        return [
            {
                "id": item.get("product_id"),
                "quantity": item.get("quantity", 1),
                "item_price": item.get("unit_price") or item.get("total_price"),
            }
            for item in items
            if item.get("product_id")
        ]
    return [{"id": content_id, "quantity": 1} for content_id in content_ids or []]


def build_tiktok_contents(items: list[dict[str, Any]] | None, content_ids: list[str] | None = None) -> list[dict[str, Any]]:
    if items:
        return [
            {
                "content_id": item.get("product_id"),
                "content_name": item.get("title_ar") or item.get("content_name"),
                "content_type": "product",
                "quantity": item.get("quantity", 1),
                "price": item.get("unit_price") or item.get("total_price"),
            }
            for item in items
            if item.get("product_id")
        ]
    return [{"content_id": content_id, "content_type": "product", "quantity": 1} for content_id in content_ids or []]


def build_tracking_event_from_order(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_name": "Purchase",
        "event_id": payload["event_id"],
        "event_time": event_time_seconds(),
        "source_url": payload.get("source_url") or payload.get("landing_page"),
        "referrer": payload.get("referrer"),
        "user_agent": payload.get("user_agent"),
        "ip_address": payload.get("ip_address"),
        "customer_name": payload.get("customer_name"),
        "phone_e164": payload.get("phone_e164"),
        "phone_digits": payload.get("phone_digits"),
        "value": payload.get("total"),
        "currency": normalize_currency_code(payload.get("currency"), payload.get("market_code")),
        "market_code": payload.get("market_code"),
        "items": payload.get("items") or [],
        "order_id": payload.get("public_order_id"),
        "fbp": payload.get("fbp"),
        "fbc": payload.get("fbc"),
        "fbclid": payload.get("fbclid"),
        "ttp": payload.get("ttp"),
        "ttclid": payload.get("ttclid"),
        "sc_click_id": payload.get("sc_click_id"),
        "sc_cookie1": payload.get("sc_cookie1"),
    }


def build_meta_payload(event: dict[str, Any], settings: Settings) -> dict[str, Any]:
    user_data: dict[str, Any] = {
        "client_ip_address": event.get("ip_address"),
        "client_user_agent": event.get("user_agent"),
        "fbp": event.get("fbp"),
        "fbc": event.get("fbc"),
    }
    phone_hash = hashed_phone(event.get("phone_digits"), event.get("phone_e164"))
    if phone_hash:
        user_data["ph"] = [phone_hash]
    user_data.update(hashed_name_parts(event.get("customer_name") or event.get("name")))
    user_data = {key: value for key, value in user_data.items() if value}

    items = event.get("items") or []
    content_ids = event.get("content_ids") or ([event["product_id"]] if event.get("product_id") else [])
    custom_data: dict[str, Any] = {
        "currency": normalize_currency_code(event.get("currency"), event.get("market_code")),
        "value": event.get("value"),
        "content_ids": [item.get("product_id") for item in items if item.get("product_id")] or content_ids,
        "content_name": event.get("content_name"),
        "contents": build_contents(items, content_ids),
        "num_items": sum(int(item.get("quantity", 1)) for item in items) if items else len(content_ids),
        "order_id": event.get("order_id"),
    }
    custom_data = {key: value for key, value in custom_data.items() if value not in (None, [], "")}

    body = {
        "data": [
            {
                "event_name": META_EVENTS.get(event["event_name"], event["event_name"]),
                "event_time": int(event.get("event_time") or event_time_seconds()),
                "event_id": event["event_id"],
                "action_source": "website",
                "event_source_url": event.get("source_url") or settings.frontend_url,
                "user_data": user_data,
                "custom_data": custom_data,
            }
        ],
        "access_token": settings.meta_access_token,
    }
    if settings.meta_test_event_code:
        body["test_event_code"] = settings.meta_test_event_code
    return body


def build_tiktok_payload(event: dict[str, Any], settings: Settings) -> dict[str, Any]:
    user: dict[str, Any] = {
        "phone_number": hash_tiktok_phone(
            event.get("phone_digits"),
            event.get("phone_e164"),
            settings.tiktok_phone_hash_mode,
        ),
        "ttp": event.get("ttp"),
    }
    user = {key: value for key, value in user.items() if value}

    context: dict[str, Any] = {
        "ip": event.get("ip_address"),
        "user_agent": event.get("user_agent"),
        "page": {
            "url": event.get("source_url") or settings.frontend_url,
            "referrer": event.get("referrer"),
        },
        "user": user,
    }
    if event.get("ttclid"):
        context["ad"] = {"callback": event["ttclid"]}
    context = {key: value for key, value in context.items() if value}

    items = event.get("items") or []
    content_ids = event.get("content_ids") or ([event["product_id"]] if event.get("product_id") else [])
    properties: dict[str, Any] = {
        "currency": normalize_currency_code(event.get("currency"), event.get("market_code")),
        "value": event.get("value"),
        "content_type": "product",
        "contents": build_tiktok_contents(items, content_ids),
        "description": event.get("content_name"),
    }
    properties = {key: value for key, value in properties.items() if value not in (None, [], "")}

    timestamp = datetime.fromtimestamp(int(event.get("event_time") or event_time_seconds()), UTC).isoformat()
    body: dict[str, Any] = {
        "pixel_code": settings.tiktok_pixel_code,
        "event": TIKTOK_EVENTS.get(event["event_name"], event["event_name"]),
        "event_id": event["event_id"],
        "timestamp": timestamp,
        "context": context,
        "properties": properties,
    }
    if settings.tiktok_test_event_code:
        body["test_event_code"] = settings.tiktok_test_event_code
    return body


def build_snap_payload(event: dict[str, Any], settings: Settings) -> dict[str, Any]:
    user_data: dict[str, Any] = {
        "ph": hashed_phone(event.get("phone_digits"), event.get("phone_e164")),
        "client_ip_address": event.get("ip_address"),
        "client_user_agent": event.get("user_agent"),
        "sc_click_id": event.get("sc_click_id"),
        "sc_cookie1": event.get("sc_cookie1"),
    }
    user_data.update(hashed_name_parts(event.get("customer_name") or event.get("name")))
    user_data = {key: value for key, value in user_data.items() if value}

    items = event.get("items") or []
    content_ids = event.get("content_ids") or ([event["product_id"]] if event.get("product_id") else [])
    custom_data: dict[str, Any] = {
        "currency": normalize_currency_code(event.get("currency"), event.get("market_code")),
        "value": event.get("value"),
        "content_ids": [item.get("product_id") for item in items if item.get("product_id")] or content_ids,
        "contents": build_contents(items, content_ids),
        "order_id": event.get("order_id"),
        "custom_fields": {
            "canonical_event_name": event["event_name"],
            **(event.get("metadata") or {}),
        },
    }
    custom_data = {key: value for key, value in custom_data.items() if value not in (None, [], "")}

    event_payload: dict[str, Any] = {
        "event_name": SNAP_EVENTS.get(event["event_name"], event["event_name"]),
        "event_time": int(event.get("event_time_ms") or event_time_milliseconds()),
        "event_id": event["event_id"],
        "action_source": "WEB",
        "event_source_url": event.get("source_url") or settings.frontend_url,
        "user_data": user_data,
        "custom_data": custom_data,
    }
    if settings.snap_test_event_code:
        event_payload["test_event_code"] = settings.snap_test_event_code
    return {"data": [event_payload]}


def send_meta_event(event: dict[str, Any], settings: Settings) -> tuple[bool, int | None, str | None]:
    if not settings.enable_capi or not settings.meta_pixel_id or not settings.meta_access_token:
        return False, None, "Meta CAPI disabled or missing credentials."
    url = f"https://graph.facebook.com/{settings.meta_graph_version}/{settings.meta_pixel_id}/events"
    return _post_json(url, build_meta_payload(event, settings))


def send_tiktok_event(event: dict[str, Any], settings: Settings) -> tuple[bool, int | None, str | None]:
    if not settings.enable_capi or not settings.tiktok_pixel_code or not settings.tiktok_access_token:
        return False, None, "TikTok Events API disabled or missing credentials."
    if event["event_name"] == "PageView":
        return False, None, "TikTok PageView is sent by the browser pixel only to avoid duplicate page views."
    return _post_json(
        settings.tiktok_events_api_url,
        build_tiktok_payload(event, settings),
        headers={"Access-Token": settings.tiktok_access_token},
    )


def send_snap_event(event: dict[str, Any], settings: Settings) -> tuple[bool, int | None, str | None]:
    if not settings.enable_capi or not settings.snap_pixel_id or not settings.snap_access_token:
        return False, None, "Snap CAPI disabled or missing credentials."
    url = f"https://tr.snapchat.com/v3/{settings.snap_pixel_id}/events"
    return _post_json(url, build_snap_payload(event, settings), params={"access_token": settings.snap_access_token})


def send_all_platform_events(event: dict[str, Any], settings: Settings) -> list[tuple[str, str, bool, int | None, str | None]]:
    return [
        ("meta", META_EVENTS.get(event["event_name"], event["event_name"]), *send_meta_event(event, settings)),
        ("tiktok", TIKTOK_EVENTS.get(event["event_name"], event["event_name"]), *send_tiktok_event(event, settings)),
        ("snapchat", SNAP_EVENTS.get(event["event_name"], event["event_name"]), *send_snap_event(event, settings)),
    ]


def _post_json(
    url: str,
    body: dict[str, Any],
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
) -> tuple[bool, int | None, str | None]:
    try:
        with httpx.Client(timeout=8) as client:
            response = client.post(url, json=body, headers=headers, params=params)
        return response.is_success, response.status_code, response.text[:1000]
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)
