"""
URL validation helpers.
"""
import ipaddress
from typing import List, Optional, Tuple
from urllib.parse import urlparse


MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = {"http", "https"}


def _is_ip_address(host: str) -> Tuple[bool, Optional[object]]:
    try:
        return True, ipaddress.ip_address(host)
    except ValueError:
        return False, None


def _is_restricted_host(host: str) -> bool:
    normalized = host.lower().strip(".")
    if not normalized:
        return True
    if normalized == "localhost" or normalized.endswith(".local"):
        return True

    is_ip, parsed = _is_ip_address(normalized)
    if not is_ip:
        return False

    return (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )


def _in_allowlist(host: str, allowlist: List[str]) -> bool:
    normalized = host.lower()
    entries = [entry.lower().strip() for entry in allowlist if entry and str(entry).strip()]
    for entry in entries:
        if normalized == entry or normalized.endswith(f".{entry}"):
            return True
    return False


def validate_url(
    url: str,
    security_mode: str = "loose",
    allowlist: Optional[List[str]] = None,
    max_length: int = MAX_URL_LENGTH,
) -> Optional[str]:
    """
    Validate URL according to configured security mode.

    Returns:
        None if valid, otherwise error message.
    """
    if not url or not str(url).strip():
        return "URL cannot be empty"

    url = str(url).strip()
    if len(url) > max_length:
        return f"URL length exceeds max limit ({max_length})"

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return "Only http/https URLs are supported"

    if not parsed.netloc:
        return "URL must include a host"

    host = (parsed.hostname or "").strip().lower()
    if not host:
        return "URL must include a valid host"

    mode = (security_mode or "loose").strip().lower()
    allowlist = allowlist or []

    if mode == "restricted" and _is_restricted_host(host):
        return f"Blocked by restricted mode: {host}"

    if mode == "allowlist" and not _in_allowlist(host, allowlist):
        return f"Host is not allowlisted: {host}"

    return None

