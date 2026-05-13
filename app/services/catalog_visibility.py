from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CatalogVisibility
from app.schemas.orders import OrderItemIn
from app.services.catalog import PACKS, PRODUCTS


VALID_ITEM_TYPES = {"product", "pack"}


def hidden_catalog_ids(db: Session) -> dict[str, set[str]]:
    rows = db.scalars(select(CatalogVisibility).where(CatalogVisibility.hidden.is_(True))).all()
    return {
        "product": {row.item_id for row in rows if row.item_type == "product"},
        "pack": {row.item_id for row in rows if row.item_type == "pack"},
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


def assert_order_items_visible(db: Session, items: list[OrderItemIn]) -> None:
    hidden = hidden_catalog_ids(db)
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
