"""
Tests for URL validation rules.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import url_validator


def test_validate_url_accepts_https():
    assert url_validator.validate_url("https://example.com/feed.xml") is None


def test_validate_url_rejects_non_http_scheme():
    error = url_validator.validate_url("ftp://example.com/feed.xml")
    assert error is not None
    assert "http/https" in error


def test_validate_url_rejects_empty_url():
    error = url_validator.validate_url("")
    assert error is not None
    assert "empty" in error.lower()


def test_validate_url_rejects_too_long_url():
    long_url = "https://example.com/" + ("a" * 2100)
    error = url_validator.validate_url(long_url)
    assert error is not None
    assert "max limit" in error


def test_validate_url_restricted_mode_blocks_localhost():
    error = url_validator.validate_url("http://localhost/rss", security_mode="restricted")
    assert error is not None
    assert "restricted" in error


def test_validate_url_allowlist_mode_requires_match():
    error = url_validator.validate_url(
        "https://news.example.com/rss",
        security_mode="allowlist",
        allowlist=["trusted.com"],
    )
    assert error is not None
    assert "allowlisted" in error


def test_validate_url_allowlist_mode_accepts_subdomain():
    error = url_validator.validate_url(
        "https://news.trusted.com/rss",
        security_mode="allowlist",
        allowlist=["trusted.com"],
    )
    assert error is None
