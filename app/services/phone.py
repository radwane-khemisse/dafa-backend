import re


class PhoneValidationError(ValueError):
    pass


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

