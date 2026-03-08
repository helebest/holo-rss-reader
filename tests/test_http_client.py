"""
Tests for HTTP client helpers.
"""
from pathlib import Path
import sys

import requests
import responses

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import http_client


@responses.activate
def test_fetch_text_does_not_touch_apparent_encoding_after_stream_consumed(monkeypatch):
    body = b"<?xml version=\"1.0\"?><rss><channel><title>Test</title></channel></rss>"

    responses.add(
        responses.GET,
        "https://example.com/feed.xml",
        body=body,
        status=200,
        content_type="application/xml",
    )

    def _boom(_self):
        raise AssertionError("response.apparent_encoding should not be accessed")

    monkeypatch.setattr(requests.models.Response, "apparent_encoding", property(_boom))

    result = http_client.fetch_text("https://example.com/feed.xml")

    assert result.ok is True
    assert "<title>Test</title>" in result.text


@responses.activate
def test_fetch_text_detects_encoding_from_xml_declaration():
    body = (
        b'<?xml version="1.0" encoding="iso-8859-1"?>\n'
        b"<rss><channel><title>caf\xe9</title></channel></rss>"
    )

    responses.add(
        responses.GET,
        "https://example.com/latin1.xml",
        body=body,
        status=200,
        content_type="application/xml",
    )

    result = http_client.fetch_text("https://example.com/latin1.xml")

    assert result.ok is True
    assert "café" in result.text
