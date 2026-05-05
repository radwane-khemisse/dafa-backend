import hashlib


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()

