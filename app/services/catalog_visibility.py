from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CatalogMarketVisibility, CatalogVisibility, ProductUpsell
from app.schemas.orders import OrderItemIn
from app.services.catalog import PACKS, PRODUCTS
from app.services.markets import normalize_market_code, valid_market_codes
from app.services.offer_pricing import get_product_market_details


VALID_ITEM_TYPES = {"product", "pack"}
DEFAULT_MARKET_CODES: dict[tuple[str, str], set[str]] = {
    ("product", "mini_portable_blender"): {"ksa"},
    ("product", "electric_meat_grinder"): {"ksa"},
}


def hidden_catalog_ids(db: Session, market_code: str | None = None) -> dict[str, set[str]]:
    code = normalize_market_code(market_code)
    rows = db.scalars(select(CatalogVisibility).where(CatalogVisibility.hidden.is_(True))).all()
    all_market_rows = db.scalars(select(CatalogMarketVisibility)).all()
    market_rows = [row for row in all_market_rows if row.market_code == code and row.visible is False]
    configured_items = {(row.item_type, row.item_id) for row in all_market_rows}
    default_hidden_products = {
        product_id
        for product_id in PRODUCTS
        if ("product", product_id) not in configured_items and code not in _default_market_codes("product", product_id)
    }
    default_hidden_packs = {
        pack_id
        for pack_id in PACKS
        if ("pack", pack_id) not in configured_items and code not in _default_market_codes("pack", pack_id)
    }
    return {
        "product": {row.item_id for row in rows if row.item_type == "product"}
        | {row.item_id for row in market_rows if row.item_type == "product"}
        | default_hidden_products,
        "pack": {row.item_id for row in rows if row.item_type == "pack"}
        | {row.item_id for row in market_rows if row.item_type == "pack"}
        | default_hidden_packs,
    }


def get_catalog_visibility(db: Session) -> dict[tuple[str, str], bool]:
    rows = db.scalars(select(CatalogVisibility)).all()
    return {(row.item_type, row.item_id): row.hidden for row in rows}


def set_catalog_hidden(db: Session, item_type: str, item_id: str, hidden: bool) -> CatalogVisibility:
    _validate_catalog_item(item_type, item_id)
    row = db.scalar(
        select(CatalogVisibility).where(
            CatalogVisibility.item_type == item_type,
            CatalogVisibility.item_id == item_id,
        )
    )
    if row is None:
        row = CatalogVisibility(item_type=item_type, item_id=item_id, hidden=hidden)
        db.add(row)
    else:
        row.hidden = hidden
    db.commit()
    db.refresh(row)
    return row


def item_market_codes(db: Session, item_type: str, item_id: str) -> list[str]:
    _validate_catalog_item(item_type, item_id)
    codes = sorted(valid_market_codes())
    rows = db.scalars(
        select(CatalogMarketVisibility).where(
            CatalogMarketVisibility.item_type == item_type,
            CatalogMarketVisibility.item_id == item_id,
        )
    ).all()
    if not rows:
        return [code for code in codes if code in _default_market_codes(item_type, item_id)]
    visible_by_market = {row.market_code: row.visible for row in rows}
    return [code for code in codes if visible_by_market.get(code, True)]


def set_catalog_market_codes(db: Session, item_type: str, item_id: str, market_codes: list[str]) -> list[CatalogMarketVisibility]:
    _validate_catalog_item(item_type, item_id)
    selected = {normalize_market_code(code) for code in market_codes}
    rows: list[CatalogMarketVisibility] = []
    for code in sorted(valid_market_codes()):
        row = db.scalar(
            select(CatalogMarketVisibility).where(
                CatalogMarketVisibility.item_type == item_type,
                CatalogMarketVisibility.item_id == item_id,
                CatalogMarketVisibility.market_code == code,
            )
        )
        if row is None:
            row = CatalogMarketVisibility(item_type=item_type, item_id=item_id, market_code=code, visible=code in selected)
            db.add(row)
        else:
            row.visible = code in selected
        rows.append(row)
    db.commit()
    return rows


def product_upsells(db: Session, market_code: str | None = None) -> dict[str, list[str]]:
    code = normalize_market_code(market_code)
    rows = db.scalars(select(ProductUpsell).where(ProductUpsell.market_code == code)).all()
    upsells: dict[str, list[str]] = {}
    for row in rows:
        if row.source_product_id in PRODUCTS and row.target_product_id in PRODUCTS:
            upsells.setdefault(row.source_product_id, []).append(row.target_product_id)
    return {source_id: sorted(set(target_ids)) for source_id, target_ids in upsells.items()}


def product_upsells_by_market(db: Session, product_id: str) -> dict[str, list[str]]:
    _validate_catalog_item("product", product_id)
    rows = db.scalars(select(ProductUpsell).where(ProductUpsell.source_product_id == product_id)).all()
    upsells = {code: [] for code in sorted(valid_market_codes())}
    for row in rows:
        if row.target_product_id in PRODUCTS:
            upsells.setdefault(row.market_code, []).append(row.target_product_id)
    return {code: sorted(set(target_ids)) for code, target_ids in upsells.items()}


def set_product_upsells(db: Session, source_product_id: str, market_code: str | None, target_product_ids: list[str]) -> list[ProductUpsell]:
    _validate_catalog_item("product", source_product_id)
    code = normalize_market_code(market_code)
    selected = list(dict.fromkeys(target_product_ids))
    product_details = get_product_market_details(db, code)
    source_warehouse = _product_warehouse(product_details, source_product_id)

    for target_product_id in selected:
        _validate_catalog_item("product", target_product_id)
        if target_product_id == source_product_id:
            raise ValueError("A product cannot upsell itself")
        if _product_warehouse(product_details, target_product_id) != source_warehouse:
            raise ValueError("Upsell products must belong to the same warehouse")

    existing = db.scalars(
        select(ProductUpsell).where(
            ProductUpsell.source_product_id == source_product_id,
            ProductUpsell.market_code == code,
        )
    ).all()
    existing_by_target = {row.target_product_id: row for row in existing}

    for row in existing:
        if row.target_product_id not in selected:
            db.delete(row)

    rows: list[ProductUpsell] = []
    for target_product_id in selected:
        row = existing_by_target.get(target_product_id)
        if row is None:
            row = ProductUpsell(source_product_id=source_product_id, target_product_id=target_product_id, market_code=code)
            db.add(row)
        rows.append(row)
    db.commit()
    return rows


def assert_order_items_visible(db: Session, items: list[OrderItemIn], market_code: str | None = None) -> None:
    hidden = hidden_catalog_ids(db, market_code)
    hidden_products = hidden["product"]
    hidden_packs = hidden["pack"]

    for item in items:
        if item.product_id in hidden_products:
            raise ValueError(f"Product is hidden and cannot be ordered: {item.product_id}")
        if item.pack_id and item.pack_id in hidden_packs:
            raise ValueError(f"Pack is hidden and cannot be ordered: {item.pack_id}")
        if item.pack_id:
            pack = PACKS.get(item.pack_id)
            if pack and any(product_id in hidden_products for product_id in pack.product_ids):
                raise ValueError(f"Pack contains a hidden product and cannot be ordered: {item.pack_id}")


def _validate_catalog_item(item_type: str, item_id: str) -> None:
    if item_type not in VALID_ITEM_TYPES:
        raise ValueError("item_type must be product or pack")
    if item_type == "product" and item_id not in PRODUCTS:
        raise ValueError(f"Unknown product_id: {item_id}")
    if item_type == "pack" and item_id not in PACKS:
        raise ValueError(f"Unknown pack_id: {item_id}")


def _default_market_codes(item_type: str, item_id: str) -> set[str]:
    return DEFAULT_MARKET_CODES.get((item_type, item_id), set(valid_market_codes()))


def _product_warehouse(product_details: dict[str, dict[str, str | float]], product_id: str) -> str:
    return str(product_details.get(product_id, {}).get("warehouse") or "").strip()
