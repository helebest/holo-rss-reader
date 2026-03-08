from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import url_validator


def test_private_helpers_cover_edge_cases():
    is_ip, parsed = url_validator._is_ip_address("127.0.0.1")
    assert is_ip is True
    assert str(parsed) == "127.0.0.1"

    is_ip, parsed = url_validator._is_ip_address("example.com")
    assert is_ip is False
    assert parsed is None

    assert url_validator._is_restricted_host("") is True
    assert url_validator._is_restricted_host("localhost") is True
    assert url_validator._is_restricted_host("printer.local") is True
    assert url_validator._is_restricted_host("192.168.1.1") is True
    assert url_validator._is_restricted_host("example.com") is False

    assert url_validator._in_allowlist("news.example.com", ["example.com"]) is True
    assert url_validator._in_allowlist("example.com", ["example.com"]) is True
    assert url_validator._in_allowlist("example.net", ["example.com"]) is False


def test_validate_url_rejects_missing_or_invalid_host():
    assert "host" in url_validator.validate_url("https:///path")
    assert "host" in url_validator.validate_url("https://")
