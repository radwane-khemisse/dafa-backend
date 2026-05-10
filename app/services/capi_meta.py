from app.core.config import Settings
from app.services.tracking import build_tracking_event_from_order, send_meta_event


def send_meta_purchase(payload: dict, settings: Settings) -> tuple[bool, int | None, str | None]:
    return send_meta_event(build_tracking_event_from_order(payload), settings)
