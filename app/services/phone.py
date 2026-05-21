import re

from app.services.markets import GULF_MARKETS, normalize_market_code


class PhoneValidationError(ValueError):
    pass


MOBILE_RULES = {
    "ksa": {"pattern": r"5\d{8}", "example": "05XXXXXXXX"},
    "kwt": {"pattern": r"(?:41|5|6|9)\d{6}", "example": "5XXXXXXX"},
    "uae": {"pattern": r"5\d{8}", "example": "05XXXXXXXX"},
    "qat": {"pattern": r"[3567]\d{7}", "example": "5XXXXXXX"},
    "bhr": {"pattern": r"3\d{7}", "example": "3XXXXXXX"},
    "omn": {"pattern": r"[79]\d{7}", "example": "9XXXXXXX"},
}


def normalize_ksa_phone(raw_phone: str) -> tuple[str, str]:
    digits = re.sub(r"\D+", "", raw_phone or "")

    if digits.startswith("00966"):
        digits = digits[2:]
    if digits.startswith("9660"):
        digits = "966" + digits[4:]
    elif digits.startswith("05"):
        digits = "966" + digits[1:]
    elif digits.startswith("5"):
        digits = "966" + digits

    if not re.fullmatch(r"9665\d{8}", digits):
        raise PhoneValidationError("Phone must be a valid Saudi mobile number.")

    local = digits[3:]
    if len(set(local)) <= 2:
        raise PhoneValidationError("Phone number appears invalid.")

    return f"+{digits}", digits


def normalize_gulf_phone(raw_phone: str, market_code: str | None = None) -> tuple[str, str]:
    code = normalize_market_code(market_code)
    market = GULF_MARKETS[code]
    rule = MOBILE_RULES[code]
    digits = re.sub(r"\D+", "", raw_phone or "")
    country_prefix = market.phone_country_code

    if digits.startswith(f"00{country_prefix}"):
        digits = digits[2:]
    if digits.startswith(f"{country_prefix}0"):
        digits = country_prefix + digits[len(country_prefix) + 1 :]
    elif digits.startswith("0") and len(digits) == market.local_phone_digits + 1:
        digits = country_prefix + digits[1:]
    elif len(digits) == market.local_phone_digits:
        digits = country_prefix + digits

    local = digits[len(country_prefix) :]
    if not digits.startswith(country_prefix) or len(local) != market.local_phone_digits or not re.fullmatch(rule["pattern"], local):
        raise PhoneValidationError(f"Phone must be a valid {market.country_name_en} mobile number, for example {rule['example']}.")
    if len(set(local)) <= 2:
        raise PhoneValidationError("Phone number appears invalid.")

    return f"+{digits}", digits
