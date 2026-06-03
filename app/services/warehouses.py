from app.services.markets import normalize_market_code


WAREHOUSES_BY_MARKET: dict[str, tuple[str, ...]] = {
    "kwt": ("COD NETWORK - Kuwait Warehouse KWT",),
    "ksa": (
        "COD NETWORK - RUH 2 Warehouse KSA",
        "COD Network - KSA 3",
        "COD NETWORK - Riyadh Warehouse KSA",
    ),
    "uae": (
        "COD NETWORK - Dubai Warehouse UAE",
        "COD NETWORK - Warehouse UAE IQ",
    ),
    "qat": (
        "COD NETWORK - Qatar Warehouse QAT",
        "COD NETWORK - Warehouse Qatar 2",
    ),
    "bhr": (
        "COD NETWORK - Bahrain Warehouse",
        "COD NETWORK - Warehouse BH IQ",
    ),
    "omn": ("COD Network Oman 1",),
}


def warehouses_for_market(market_code: str | None) -> tuple[str, ...]:
    return WAREHOUSES_BY_MARKET[normalize_market_code(market_code)]


def default_warehouse_for_market(market_code: str | None) -> str:
    return warehouses_for_market(market_code)[0]


def normalize_warehouse(market_code: str | None, warehouse: str | None) -> str:
    value = (warehouse or "").strip()
    allowed = warehouses_for_market(market_code)
    if not value:
        return allowed[0]
    if value not in allowed:
        raise ValueError(f"Unknown warehouse for market {normalize_market_code(market_code)}: {value}")
    return value
