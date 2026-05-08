import ipaddress
from dataclasses import dataclass
from functools import lru_cache

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class IpValidation:
    ip_address: str | None
    country_code: str | None = None
    city: str | None = None
    is_vpn: bool | None = None
    is_valid_ksa: bool = False
    reason: str = "not_checked"


def client_ip_from_request(request, fallback: str | None = None) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return fallback or (request.client.host if request.client else None)


def validate_ip(ip_address: str | None, settings: Settings) -> IpValidation:
    if not ip_address:
        return IpValidation(ip_address=None, reason="missing_ip")

    try:
        parsed_ip = ipaddress.ip_address(ip_address)
    except ValueError:
        return IpValidation(ip_address=ip_address, reason="invalid_ip")

    if parsed_ip.is_private or parsed_ip.is_loopback:
        return IpValidation(
            ip_address=ip_address,
            country_code=settings.analytics_target_country if settings.analytics_allow_private_ips else None,
            is_vpn=False,
            is_valid_ksa=settings.analytics_allow_private_ips,
            reason="private_ip_allowed" if settings.analytics_allow_private_ips else "private_ip",
        )

    geo = _lookup_maxmind(ip_address, settings)
    vpn = geo.get("is_vpn")
    vpn_source = geo.get("vpn_source")

    provider_vpn = _lookup_vpn_provider(ip_address, settings)
    if provider_vpn is not None:
        vpn = provider_vpn
        vpn_source = "vpn_provider"

    country_code = geo.get("country_code")
    is_vpn = bool(vpn) if vpn is not None else None
    is_valid = country_code == settings.analytics_target_country and is_vpn is not True

    if not country_code:
        reason = "maxmind_not_configured_or_no_match"
    elif country_code != settings.analytics_target_country:
        reason = f"country_{country_code}"
    elif is_vpn is True:
        reason = f"vpn_detected_{vpn_source or 'unknown'}"
    elif is_vpn is None:
        reason = "valid_country_vpn_unknown"
    else:
        reason = "valid_ksa"

    return IpValidation(
        ip_address=ip_address,
        country_code=country_code,
        city=geo.get("city"),
        is_vpn=is_vpn,
        is_valid_ksa=is_valid,
        reason=reason,
    )


def _lookup_maxmind(ip_address: str, settings: Settings) -> dict:
    result: dict = {}
    try:
        import geoip2.database
        from geoip2.errors import AddressNotFoundError
    except ImportError:
        return result

    country_db = settings.maxmind_city_db_path or settings.maxmind_country_db_path
    if country_db:
        try:
            with geoip2.database.Reader(country_db) as reader:
                response = reader.city(ip_address) if settings.maxmind_city_db_path else reader.country(ip_address)
                result["country_code"] = response.country.iso_code
                result["city"] = getattr(getattr(response, "city", None), "name", None)
        except (FileNotFoundError, AddressNotFoundError, ValueError):
            pass

    if settings.maxmind_anonymous_ip_db_path:
        try:
            with geoip2.database.Reader(settings.maxmind_anonymous_ip_db_path) as reader:
                response = reader.anonymous_ip(ip_address)
                result["is_vpn"] = bool(
                    response.is_anonymous
                    or response.is_anonymous_vpn
                    or response.is_hosting_provider
                    or response.is_public_proxy
                    or response.is_tor_exit_node
                )
                result["vpn_source"] = "maxmind_anonymous_ip"
        except (FileNotFoundError, AddressNotFoundError, ValueError):
            pass

    return result


def _lookup_vpn_provider(ip_address: str, settings: Settings) -> bool | None:
    if not settings.vpn_check_url:
        return None

    headers = {}
    if settings.vpn_check_api_key:
        value = settings.vpn_check_api_key
        if settings.vpn_check_api_key_header.lower() == "authorization" and not value.lower().startswith("bearer "):
            value = f"Bearer {value}"
        headers[settings.vpn_check_api_key_header] = value

    try:
        with httpx.Client(timeout=2.5) as client:
            response = client.get(settings.vpn_check_url.format(ip=ip_address), headers=headers)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    for key in ("is_vpn", "vpn", "proxy", "tor", "is_proxy", "is_datacenter"):
        value = data.get(key)
        if isinstance(value, bool):
            return value
    security = data.get("security")
    if isinstance(security, dict):
        return any(bool(security.get(key)) for key in ("vpn", "proxy", "tor", "relay"))
    return None


@lru_cache(maxsize=256)
def cached_validate_ip(ip_address: str | None, app_env: str) -> IpValidation:
    from app.core.config import get_settings

    return validate_ip(ip_address, get_settings())
