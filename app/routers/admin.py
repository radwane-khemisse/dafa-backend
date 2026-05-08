import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import case, desc, distinct, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.models import AnalyticsEvent, Order, OrderItem
from app.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    settings = get_settings()
    expected_username = settings.admin_username
    expected_password = settings.admin_password
    if not expected_username or not expected_password:
        raise HTTPException(status_code=503, detail="Admin credentials are not configured")

    username_ok = secrets.compare_digest(credentials.username, expected_username)
    password_ok = secrets.compare_digest(credentials.password, expected_password)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def _date_range(start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    range_end = end or now
    range_start = start or (range_end - timedelta(days=7))
    if range_start > range_end:
        raise HTTPException(status_code=422, detail="start must be before end")
    return range_start, range_end


@router.get("/dashboard")
def dashboard(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
) -> dict:
    range_start, range_end = _date_range(start, end)
    event_filter = (
        AnalyticsEvent.created_at >= range_start,
        AnalyticsEvent.created_at <= range_end,
        AnalyticsEvent.ip_is_valid_ksa.is_(True),
    )
    order_filter = (
        Order.created_at >= range_start,
        Order.created_at <= range_end,
        Order.ip_is_valid_ksa.is_(True),
    )

    clicks = db.scalar(select(func.count()).select_from(AnalyticsEvent).where(*event_filter, AnalyticsEvent.event_name == "Click")) or 0
    product_views = db.scalar(select(func.count()).select_from(AnalyticsEvent).where(*event_filter, AnalyticsEvent.event_name == "ViewProduct")) or 0
    add_to_cart = db.scalar(select(func.count()).select_from(AnalyticsEvent).where(*event_filter, AnalyticsEvent.event_name == "AddToCart")) or 0
    checkout = db.scalar(select(func.count()).select_from(AnalyticsEvent).where(*event_filter, AnalyticsEvent.event_name == "InitiateCheckout")) or 0
    visitors = db.scalar(select(func.count(distinct(AnalyticsEvent.session_id))).where(*event_filter)) or 0
    orders = db.scalar(select(func.count()).select_from(Order).where(*order_filter)) or 0
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(*order_filter)) or 0
    aov = round(revenue / orders, 2) if orders else 0
    conversion_rate = round((orders / visitors) * 100, 2) if visitors else 0
    checkout_rate = round((checkout / visitors) * 100, 2) if visitors else 0
    cart_rate = round((add_to_cart / visitors) * 100, 2) if visitors else 0

    daily_rows = db.execute(
        select(
            func.date(AnalyticsEvent.created_at).label("day"),
            func.count(case((AnalyticsEvent.event_name == "Click", 1))).label("clicks"),
            func.count(case((AnalyticsEvent.event_name == "AddToCart", 1))).label("add_to_cart"),
            func.count(case((AnalyticsEvent.event_name == "InitiateCheckout", 1))).label("checkout"),
            func.count(distinct(AnalyticsEvent.session_id)).label("visitors"),
        )
        .where(*event_filter)
        .group_by(func.date(AnalyticsEvent.created_at))
        .order_by(func.date(AnalyticsEvent.created_at))
    ).all()
    order_daily_rows = {
        str(row.day): row
        for row in db.execute(
            select(
                func.date(Order.created_at).label("day"),
                func.count(Order.id).label("orders"),
                func.coalesce(func.sum(Order.total), 0).label("revenue"),
            )
            .where(*order_filter)
            .group_by(func.date(Order.created_at))
        ).all()
    }

    top_products = db.execute(
        select(OrderItem.product_id, OrderItem.title_ar, func.count(OrderItem.id), func.coalesce(func.sum(OrderItem.total_price), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .where(*order_filter)
        .group_by(OrderItem.product_id, OrderItem.title_ar)
        .order_by(desc(func.count(OrderItem.id)))
        .limit(8)
    ).all()

    top_campaigns = db.execute(
        select(
            func.coalesce(AnalyticsEvent.utm_campaign, "direct").label("campaign"),
            func.count().label("events"),
            func.count(distinct(AnalyticsEvent.session_id)).label("visitors"),
        )
        .where(*event_filter)
        .group_by(func.coalesce(AnalyticsEvent.utm_campaign, "direct"))
        .order_by(desc(func.count()))
        .limit(8)
    ).all()

    recent_orders = _serialize_orders(
        db.scalars(
            select(Order)
            .options(selectinload(Order.items))
            .where(*order_filter)
            .order_by(desc(Order.created_at))
            .limit(10)
        ).all()
    )

    return {
        "range": {"start": range_start.isoformat(), "end": range_end.isoformat()},
        "metrics": {
            "visitors": visitors,
            "clicks": clicks,
            "product_views": product_views,
            "add_to_cart": add_to_cart,
            "checkout": checkout,
            "orders": orders,
            "revenue": revenue,
            "aov": aov,
            "conversion_rate": conversion_rate,
            "checkout_rate": checkout_rate,
            "cart_rate": cart_rate,
        },
        "daily": [
            {
                "date": str(row.day),
                "visitors": row.visitors,
                "clicks": row.clicks,
                "add_to_cart": row.add_to_cart,
                "checkout": row.checkout,
                "orders": getattr(order_daily_rows.get(str(row.day)), "orders", 0),
                "revenue": getattr(order_daily_rows.get(str(row.day)), "revenue", 0),
            }
            for row in daily_rows
        ],
        "top_products": [
            {"product_id": row[0], "title": row[1], "orders": row[2], "revenue": row[3]} for row in top_products
        ],
        "top_campaigns": [
            {"campaign": row.campaign or "direct", "events": row.events, "visitors": row.visitors} for row in top_campaigns
        ],
        "recent_orders": recent_orders,
    }


@router.get("/orders")
def orders(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
) -> dict:
    range_start, range_end = _date_range(start, end)
    filters = [Order.created_at >= range_start, Order.created_at <= range_end, Order.ip_is_valid_ksa.is_(True)]
    if status_filter:
        filters.append(Order.status == status_filter)
    rows = db.scalars(
        select(Order)
        .options(selectinload(Order.items))
        .where(*filters)
        .order_by(desc(Order.created_at))
        .limit(200)
    ).all()
    return {"orders": _serialize_orders(rows)}


def _serialize_orders(orders: list[Order]) -> list[dict]:
    return [
        {
            "id": order.id,
            "public_order_id": order.public_order_id,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "customer_name": order.customer_name,
            "phone_e164": order.phone_e164,
            "status": order.status,
            "subtotal": order.subtotal,
            "delivery_fee": order.delivery_fee,
            "discount": order.discount,
            "total": order.total,
            "currency": order.currency,
            "payment_method": order.payment_method,
            "upsell_accepted": order.upsell_accepted,
            "source_url": order.source_url,
            "referrer": order.referrer,
            "utm_source": order.utm_source,
            "utm_medium": order.utm_medium,
            "utm_campaign": order.utm_campaign,
            "utm_content": order.utm_content,
            "utm_term": order.utm_term,
            "city": order.ip_city,
            "country": order.ip_country_code,
            "items": [
                {
                    "product_id": item.product_id,
                    "title_ar": item.title_ar,
                    "offer_id": item.offer_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                }
                for item in order.items
            ],
        }
        for order in orders
    ]
