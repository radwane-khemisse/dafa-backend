from dataclasses import dataclass


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
    "upsell_99": Offer(id="upsell_99", quantity=1, total_price=99, label_ar="عرض خاص"),
}


def calculate_item(product_id: str, offer_id: str) -> dict:
    product = PRODUCTS.get(product_id)
    offer = OFFERS.get(offer_id)
    if product is None:
        raise ValueError(f"Unknown product_id: {product_id}")
    if offer is None:
        raise ValueError(f"Unknown offer_id: {offer_id}")
    return {
        "product_id": product.id,
        "title_ar": product.name_ar,
        "sku": product.sku,
        "offer_id": offer.id,
        "quantity": offer.quantity,
        "unit_price": round(offer.total_price / offer.quantity),
        "total_price": offer.total_price,
    }
