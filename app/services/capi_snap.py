from app.core.config import Settings
from app.services.tracking import build_tracking_event_from_order, send_snap_event


def send_snap_purchase(payload: dict, settings: Settings) -> tuple[bool, int | None, str | None]:
    return send_snap_event(build_tracking_event_from_order(payload), settings)
