import httpx

from app.core.config import Settings


def send_order_to_sheet(payload: dict, settings: Settings) -> tuple[bool, int | None, str | None]:
    if not settings.enable_sheets_webhook or not settings.order_webhook_url:
        return False, None, "Sheets webhook disabled or missing URL."

    body = {
        "order": payload.get("sheet_order", payload),
    }

    try:
        with httpx.Client(timeout=8) as client:
            response = client.post(settings.order_webhook_url, json=body)
        return response.is_success, response.status_code, response.text[:1000]
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)
