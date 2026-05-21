from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OfferMarketPrice
from app.services.catalog import OFFERS, PRODUCTS
from app.services.markets import normalize_market_code, valid_market_codes


PRODUCT_OFFER_IDS = ("one", "two", "three")


def default_product_offer_prices() -> dict[str, dict[str, int]]:
    return {
        product_id: {offer_id: OFFERS[offer_id].total_price for offer_id in PRODUCT_OFFER_IDS}
        for product_id in PRODUCTS
    }


def get_offer_prices(db: Session, market_code: str | None) -> dict[str, dict[str, int]]:
    code = normalize_market_code(market_code)
    prices = default_product_offer_prices()
    rows = db.scalars(select(OfferMarketPrice).where(OfferMarketPrice.market_code == code)).all()
    for row in rows:
        if row.product_id in prices and row.offer_id in prices[row.product_id]:
            prices[row.product_id][row.offer_id] = row.price
    return prices


def admin_product_offers(db: Session, product_id: str) -> list[dict]:
    if product_id not in PRODUCTS:
        raise ValueError(f"Unknown product_id: {product_id}")

    rows = db.scalars(select(OfferMarketPrice).where(OfferMarketPrice.product_id == product_id)).all()
    overrides = {(row.offer_id, row.market_code): row.price for row in rows}
    return [
        {
            "id": offer_id,
            "label_ar": OFFERS[offer_id].label_ar,
            "quantity": OFFERS[offer_id].quantity,
            "prices": {
                code: overrides.get((offer_id, code), OFFERS[offer_id].total_price)
                for code in sorted(valid_market_codes())
            },
        }
        for offer_id in PRODUCT_OFFER_IDS
    ]


def set_offer_market_price(db: Session, product_id: str, offer_id: str, market_code: str, price: int) -> OfferMarketPrice:
    if product_id not in PRODUCTS:
        raise ValueError(f"Unknown product_id: {product_id}")
    if offer_id not in PRODUCT_OFFER_IDS:
        raise ValueError(f"Unknown product offer_id: {offer_id}")
    if price < 0:
        raise ValueError("price must be zero or greater")

    code = normalize_market_code(market_code)
    row = db.scalar(
        select(OfferMarketPrice).where(
            OfferMarketPrice.product_id == product_id,
            OfferMarketPrice.offer_id == offer_id,
            OfferMarketPrice.market_code == code,
        )
    )
    if row is None:
        row = OfferMarketPrice(product_id=product_id, offer_id=offer_id, market_code=code, price=price)
        db.add(row)
    else:
        row.price = price
    db.commit()
    db.refresh(row)
    return row
