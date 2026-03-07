"""
Tests for fetcher error handling.
"""
from pathlib import Path
import sys

import pytest
import responses

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import fetcher
import http_client


class TestFetcherErrorHandling:
    """Test that fetch errors are properly reported, not silently swallowed."""

    def test_fetch_feed_returns_error_on_network_failure(self, monkeypatch):
        """Network failures should return error info."""

        def fake_fetch_text(*_args, **_kwargs):
            return http_client.HTTPResult(ok=False, error="Network error: boom", error_kind="network")

        monkeypatch.setattr(fetcher.http_client, "fetch_text", fake_fetch_text)

        result, error, meta = fetcher.fetch_feed_detailed("https://example.com/feed")

        assert result is not None
        assert error is not None
        assert "Network error" in error
        assert meta.error_kind == "network"

    def test_fetch_feed_returns_validation_error_on_bad_scheme(self):
        result, error, meta = fetcher.fetch_feed_detailed("file:///etc/passwd")

        assert result is not None
        assert error is not None
        assert "Invalid URL" in error
        assert meta.error_kind == "validation"

    @responses.activate
    def test_fetch_feed_returns_error_on_http_error(self):
        responses.add(
            responses.GET,
            "https://example.com/feed",
            body="Not Found",
            status=404,
        )

        result, error, meta = fetcher.fetch_feed_detailed("https://example.com/feed")

        assert result is not None
        assert error is not None
        assert "HTTP 404" in error
        assert meta.status_code == 404
        assert meta.error_kind == "network"

    @responses.activate
    def test_fetch_feed_respects_max_bytes_limit(self):
        responses.add(
            responses.GET,
            "https://example.com/feed",
            body="<rss>" + ("a" * 4096) + "</rss>",
            status=200,
        )

        result, error, meta = fetcher.fetch_feed_detailed(
            "https://example.com/feed",
            max_bytes=128,
        )

        assert result is not None
        assert error is not None
        assert "max size" in error
        assert meta.error_kind == "network"
