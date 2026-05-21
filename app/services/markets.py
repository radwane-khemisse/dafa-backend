from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MarketStore


@dataclass(frozen=True)
class MarketDefinition:
    code: str
    country_code: str
    country_name_ar: str
    country_name_en: str
    currency: str
    phone_country_code: str
    local_phone_digits: int


GULF_MARKETS: dict[str, MarketDefinition] = {
    "ksa": MarketDefinition("ksa", "SA", "السعودية", "Saudi Arabia", "SAR", "966", 9),
    "kwt": MarketDefinition("kwt", "KW", "الكويت", "Kuwait", "KWD", "965", 8),
    "uae": MarketDefinition("uae", "AE", "الإمارات", "United Arab Emirates", "AED", "971", 9),
    "qat": MarketDefinition("qat", "QA", "قطر", "Qatar", "QAR", "974", 8),
    "bhr": MarketDefinition("bhr", "BH", "البحرين", "Bahrain", "BHD", "973", 8),
    "omn": MarketDefinition("omn", "OM", "عمان", "Oman", "OMR", "968", 8),
}


def valid_market_codes() -> set[str]:
    return set(GULF_MARKETS)


def normalize_market_code(market_code: str | None) -> str:
    code = (market_code or "ksa").strip().lower()
    if code not in GULF_MARKETS:
        raise ValueError(f"Unknown market_code: {market_code}")
    return code


def list_market_settings(db: Session) -> list[dict]:
    rows = {row.market_code: row for row in db.scalars(select(MarketStore)).all()}
    return [market_payload(code, rows.get(code)) for code in GULF_MARKETS]


def get_market_settings(db: Session, market_code: str | None) -> dict:
    code = normalize_market_code(market_code)
    row = db.scalar(select(MarketStore).where(MarketStore.market_code == code))
    return market_payload(code, row)


def set_market_settings(db: Session, market_code: str, active: bool, currency: str) -> MarketStore:
    code = normalize_market_code(market_code)
    definition = GULF_MARKETS[code]
    normalized_currency = (currency or definition.currency).strip().upper()[:3]
    row = db.scalar(select(MarketStore).where(MarketStore.market_code == code))
    if row is None:
        row = MarketStore(
            market_code=code,
            country_code=definition.country_code,
            country_name_ar=definition.country_name_ar,
            country_name_en=definition.country_name_en,
            active=active,
            currency=normalized_currency,
        )
        db.add(row)
    else:
        row.active = active
        row.currency = normalized_currency
    db.commit()
    db.refresh(row)
    return row


def market_payload(code: str, row: MarketStore | None = None) -> dict:
    definition = GULF_MARKETS[code]
    return {
        "code": code,
        "country_code": definition.country_code,
        "country_name_ar": definition.country_name_ar,
        "country_name_en": definition.country_name_en,
        "active": row.active if row is not None else True,
        "currency": row.currency if row is not None else definition.currency,
        "phone_country_code": definition.phone_country_code,
        "local_phone_digits": definition.local_phone_digits,
    }
