from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OfferMarketPrice, PackMarketDetail, PackMarketPrice, ProductMarketDetail
from app.services.catalog import OFFERS, PACKS, PRODUCTS
from app.services.markets import normalize_market_code, valid_market_codes
from app.services.warehouses import default_warehouse_for_market, normalize_warehouse


PRODUCT_OFFER_IDS = ("one", "two", "three")
RIYADH_WAREHOUSE = "COD NETWORK - Riyadh Warehouse KSA"
PRODUCT_DEFAULT_WAREHOUSES: dict[tuple[str, str], str] = {
    ("vegetable_cutter", "ksa"): RIYADH_WAREHOUSE,
    ("mini_portable_blender", "ksa"): RIYADH_WAREHOUSE,
}


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


def default_pack_prices() -> dict[str, int]:
    return {pack_id: pack.total_price for pack_id, pack in PACKS.items()}


def get_pack_prices(db: Session, market_code: str | None) -> dict[str, int]:
    code = normalize_market_code(market_code)
    prices = default_pack_prices()
    rows = db.scalars(select(PackMarketPrice).where(PackMarketPrice.market_code == code)).all()
    for row in rows:
        if row.pack_id in prices:
            prices[row.pack_id] = row.price
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


def default_product_market_details() -> dict[str, dict[str, dict[str, str | float]]]:
    return {
        product_id: {
            code: {"sku": product.sku, "cost": 0.0, "warehouse": _default_product_warehouse(product_id, code)}
            for code in sorted(valid_market_codes())
        }
        for product_id, product in PRODUCTS.items()
    }


def get_product_market_details(db: Session, market_code: str | None) -> dict[str, dict[str, str | float]]:
    code = normalize_market_code(market_code)
    details = {
        product_id: {"sku": product.sku, "cost": 0.0, "warehouse": _default_product_warehouse(product_id, code)}
        for product_id, product in PRODUCTS.items()
    }
    rows = db.scalars(select(ProductMarketDetail).where(ProductMarketDetail.market_code == code)).all()
    for row in rows:
        if row.product_id in details:
            details[row.product_id] = {"sku": row.sku, "cost": row.cost, "warehouse": row.warehouse or _default_product_warehouse(row.product_id, code)}
    return details


def admin_product_market_details(db: Session, product_id: str) -> dict[str, dict[str, str | float]]:
    if product_id not in PRODUCTS:
        raise ValueError(f"Unknown product_id: {product_id}")
    rows = db.scalars(select(ProductMarketDetail).where(ProductMarketDetail.product_id == product_id)).all()
    overrides = {
        row.market_code: {"sku": row.sku, "cost": row.cost, "warehouse": row.warehouse or _default_product_warehouse(product_id, row.market_code)}
        for row in rows
    }
    return {
        code: overrides.get(code, {"sku": PRODUCTS[product_id].sku, "cost": 0.0, "warehouse": _default_product_warehouse(product_id, code)})
        for code in sorted(valid_market_codes())
    }


def admin_pack_prices(db: Session, pack_id: str) -> dict[str, int]:
    if pack_id not in PACKS:
        raise ValueError(f"Unknown pack_id: {pack_id}")
    rows = db.scalars(select(PackMarketPrice).where(PackMarketPrice.pack_id == pack_id)).all()
    overrides = {row.market_code: row.price for row in rows}
    return {
        code: overrides.get(code, PACKS[pack_id].total_price)
        for code in sorted(valid_market_codes())
    }


def _default_pack_sku(pack_id: str) -> str:
    return f"DAFA-{pack_id.upper().replace('-', '-')}"


def _default_product_warehouse(product_id: str, market_code: str) -> str:
    return PRODUCT_DEFAULT_WAREHOUSES.get((product_id, market_code), default_warehouse_for_market(market_code))


def get_pack_market_details(db: Session, market_code: str | None) -> dict[str, dict[str, str | float]]:
    code = normalize_market_code(market_code)
    details = {pack_id: {"sku": _default_pack_sku(pack_id), "cost": 0.0} for pack_id in PACKS}
    rows = db.scalars(select(PackMarketDetail).where(PackMarketDetail.market_code == code)).all()
    for row in rows:
        if row.pack_id in details:
            details[row.pack_id] = {"sku": row.sku, "cost": row.cost}
    return details


def admin_pack_market_details(db: Session, pack_id: str) -> dict[str, dict[str, str | float]]:
    if pack_id not in PACKS:
        raise ValueError(f"Unknown pack_id: {pack_id}")
    rows = db.scalars(select(PackMarketDetail).where(PackMarketDetail.pack_id == pack_id)).all()
    overrides = {row.market_code: {"sku": row.sku, "cost": row.cost} for row in rows}
    return {
        code: overrides.get(code, {"sku": _default_pack_sku(pack_id), "cost": 0.0})
        for code in sorted(valid_market_codes())
    }


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


def set_pack_market_price(db: Session, pack_id: str, market_code: str, price: int) -> PackMarketPrice:
    if pack_id not in PACKS:
        raise ValueError(f"Unknown pack_id: {pack_id}")
    if price < 0:
        raise ValueError("price must be zero or greater")

    code = normalize_market_code(market_code)
    row = db.scalar(
        select(PackMarketPrice).where(
            PackMarketPrice.pack_id == pack_id,
            PackMarketPrice.market_code == code,
        )
    )
    if row is None:
        row = PackMarketPrice(pack_id=pack_id, market_code=code, price=price)
        db.add(row)
    else:
        row.price = price
    db.commit()
    db.refresh(row)
    return row


def set_product_market_detail(db: Session, product_id: str, market_code: str, sku: str, cost: float, warehouse: str | None = None) -> ProductMarketDetail:
    if product_id not in PRODUCTS:
        raise ValueError(f"Unknown product_id: {product_id}")
    normalized_sku = sku.strip()
    if not normalized_sku:
        raise ValueError("sku is required")
    if cost < 0:
        raise ValueError("cost must be zero or greater")

    code = normalize_market_code(market_code)
    normalized_warehouse = normalize_warehouse(code, warehouse)
    row = db.scalar(
        select(ProductMarketDetail).where(
            ProductMarketDetail.product_id == product_id,
            ProductMarketDetail.market_code == code,
        )
    )
    if row is None:
        row = ProductMarketDetail(product_id=product_id, market_code=code, sku=normalized_sku, cost=cost, warehouse=normalized_warehouse)
        db.add(row)
    else:
        row.sku = normalized_sku
        row.cost = cost
        row.warehouse = normalized_warehouse
    db.commit()
    db.refresh(row)
    return row


def set_pack_market_detail(db: Session, pack_id: str, market_code: str, sku: str, cost: float) -> PackMarketDetail:
    if pack_id not in PACKS:
        raise ValueError(f"Unknown pack_id: {pack_id}")
    normalized_sku = sku.strip()
    if not normalized_sku:
        raise ValueError("sku is required")
    if cost < 0:
        raise ValueError("cost must be zero or greater")

    code = normalize_market_code(market_code)
    row = db.scalar(
        select(PackMarketDetail).where(
            PackMarketDetail.pack_id == pack_id,
            PackMarketDetail.market_code == code,
        )
    )
    if row is None:
        row = PackMarketDetail(pack_id=pack_id, market_code=code, sku=normalized_sku, cost=cost)
        db.add(row)
    else:
        row.sku = normalized_sku
        row.cost = cost
    db.commit()
    db.refresh(row)
    return row
