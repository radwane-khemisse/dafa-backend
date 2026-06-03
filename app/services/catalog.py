from dataclasses import dataclass
from typing import Iterable

from app.schemas.orders import OrderItemIn


@dataclass(frozen=True)
class Offer:
    id: str
    quantity: int
    total_price: int
    label_ar: str


@dataclass(frozen=True)
class Product:
    id: str
    slug: str
    name_ar: str
    name_en: str
    sku: str


@dataclass(frozen=True)
class Pack:
    id: str
    offer_id: str
    product_ids: tuple[str, ...]
    total_price: int


PRODUCTS: dict[str, Product] = {
    "dish_drying_rack": Product(
        id="dish_drying_rack",
        slug="over-sink-dish-drying-rack",
        name_ar="منظم تجفيف الصحون فوق الحوض",
        name_en="Over-Sink Dish Drying Organizer",
        sku="DAFA-DR-2658",
    ),
    "rice_dispenser": Product(
        id="rice_dispenser",
        slug="rice-dispenser",
        name_ar="حافظة الأرز الذكية مع كوب قياس",
        name_en="Smart Rice Storage Dispenser with Measuring Cup",
        sku="DAFA-RD-7394",
    ),
    "vegetable_cutter": Product(
        id="vegetable_cutter",
        slug="vegetable-cutter-set",
        name_ar="مجموعة تقطيع الخضار الاحترافية",
        name_en="Professional Vegetable Cutting Set",
        sku="DAFA-VC-4821",
    ),
}

OFFERS: dict[str, Offer] = {
    "one": Offer(id="one", quantity=1, total_price=199, label_ar="قطعة واحدة"),
    "two": Offer(id="two", quantity=2, total_price=279, label_ar="قطعتين"),
    "three": Offer(id="three", quantity=3, total_price=349, label_ar="3 قطع"),
    "pack_pair": Offer(id="pack_pair", quantity=1, total_price=159, label_ar="ضمن باقة"),
    "upsell_99": Offer(id="upsell_99", quantity=1, total_price=99, label_ar="عرض خاص"),
}

PACKS: dict[str, Pack] = {
    "prep-and-storage-pack": Pack(
        id="prep-and-storage-pack",
        offer_id="pack_pair",
        product_ids=("vegetable_cutter", "rice_dispenser"),
        total_price=318,
    ),
    "clean-counter-pack": Pack(
        id="clean-counter-pack",
        offer_id="pack_pair",
        product_ids=("vegetable_cutter", "dish_drying_rack"),
        total_price=318,
    ),
}


OfferPriceMap = dict[str, dict[str, int]]
PackPriceMap = dict[str, int]
MarketDetailMap = dict[str, dict[str, str | float]]


def calculate_items(
    items: list[OrderItemIn],
    offer_prices: OfferPriceMap | None = None,
    pack_prices: PackPriceMap | None = None,
    product_details: MarketDetailMap | None = None,
    pack_details: MarketDetailMap | None = None,
) -> list[dict]:
    calculated: list[dict] = []
    pack_groups: dict[str, list[OrderItemIn]] = {}

    for item in items:
        if item.pack_id:
            pack_groups.setdefault(item.pack_id, []).append(item)
        else:
            calculated.append(calculate_item(item.product_id, item.offer_id, offer_prices, product_details))

    for pack_id, pack_items in pack_groups.items():
        calculated.extend(calculate_pack_items(pack_id, pack_items, pack_prices, product_details, pack_details))

    return calculated


def calculate_item(
    product_id: str,
    offer_id: str,
    offer_prices: OfferPriceMap | None = None,
    product_details: MarketDetailMap | None = None,
) -> dict:
    product = PRODUCTS.get(product_id)
    offer = OFFERS.get(offer_id)
    if product is None:
        raise ValueError(f"Unknown product_id: {product_id}")
    if offer is None:
        raise ValueError(f"Unknown offer_id: {offer_id}")
    if offer.id == "pack_pair":
        raise ValueError("pack_pair requires a valid pack_id")
    total_price = offer_prices.get(product.id, {}).get(offer.id, offer.total_price) if offer_prices else offer.total_price
    return _item_payload(product, offer.id, offer.quantity, _unit_price(total_price, offer.quantity), total_price, product_details)


def calculate_pack_items(
    pack_id: str,
    items: Iterable[OrderItemIn],
    pack_prices: PackPriceMap | None = None,
    product_details: MarketDetailMap | None = None,
    pack_details: MarketDetailMap | None = None,
) -> list[dict]:
    pack = PACKS.get(pack_id)
    if pack is None:
        raise ValueError(f"Unknown pack_id: {pack_id}")

    pack_items = list(items)
    received_ids = tuple(item.product_id for item in pack_items)
    if set(received_ids) != set(pack.product_ids) or len(received_ids) != len(pack.product_ids):
        raise ValueError(f"Invalid products for pack_id: {pack_id}")

    if any(item.offer_id != pack.offer_id for item in pack_items):
        raise ValueError(f"Invalid offer for pack_id: {pack_id}")

    total_price = pack_prices.get(pack.id, pack.total_price) if pack_prices else pack.total_price
    line_totals = _split_total(total_price, len(pack_items))
    pack_detail = (pack_details or {}).get(pack.id, {})
    return [
        _item_payload(
            product=_require_product(item.product_id),
            offer_id=pack.offer_id,
            quantity=1,
            unit_price=line_totals[index],
            total_price=line_totals[index],
            product_details=product_details,
            sku_override=str(pack_detail.get("sku") or ""),
        )
        for index, item in enumerate(pack_items)
    ]


def _require_product(product_id: str) -> Product:
    product = PRODUCTS.get(product_id)
    if product is None:
        raise ValueError(f"Unknown product_id: {product_id}")
    return product


def _item_payload(
    product: Product,
    offer_id: str,
    quantity: int,
    unit_price: float,
    total_price: int,
    product_details: MarketDetailMap | None = None,
    sku_override: str = "",
) -> dict:
    detail = (product_details or {}).get(product.id, {})
    return {
        "product_id": product.id,
        "title_ar": product.name_ar,
        "sku": sku_override or str(detail.get("sku") or product.sku),
        "warehouse": str(detail.get("warehouse") or ""),
        "offer_id": offer_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
    }


def _unit_price(total_price: int, quantity: int) -> float:
    return round(total_price / quantity, 2)


def _split_total(total: int, count: int) -> list[int]:
    if count <= 0:
        return []
    base = total // count
    remainder = total - base * count
    return [base + (1 if index < remainder else 0) for index in range(count)]
