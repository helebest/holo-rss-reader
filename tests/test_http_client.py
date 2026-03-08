"""
Tests for HTTP client helpers.
"""
from pathlib import Path
import sys

import requests
import responses
from urllib3.util.retry import Retry

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


def test_build_session_does_not_retry_429_or_wait_retry_after():
    session = http_client.build_session(retries=1)
    adapter = session.get_adapter("https://")
    retry = adapter.max_retries

    assert isinstance(retry, Retry)
    assert 429 not in retry.status_forcelist
    assert retry.respect_retry_after_header is False


@responses.activate
def test_fetch_text_retries_once_direct_on_proxy_429(monkeypatch):
    url = "https://example.com/rate-limited.xml"
    proxy_session = requests.Session()
    proxy_session.trust_env = True

    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1235")

    responses.add(
        responses.GET,
        url,
        body="Too Many Requests",
        status=429,
        headers={"Retry-After": "3600"},
    )
    responses.add(
        responses.GET,
        url,
        body=b"<?xml version='1.0'?><rss><channel><title>Recovered</title></channel></rss>",
        status=200,
        content_type="application/xml",
    )

    result = http_client.fetch_text(url, session=proxy_session)

    assert result.ok is True
    assert "Recovered" in result.text
    assert len(responses.calls) == 2


@responses.activate
def test_fetch_text_returns_429_when_direct_retry_also_fails(monkeypatch):
    url = "https://example.com/still-bad.xml"
    proxy_session = requests.Session()
    proxy_session.trust_env = True

    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1235")

    responses.add(
        responses.GET,
        url,
        body="Too Many Requests",
        status=429,
        headers={"Retry-After": "3600"},
    )
    responses.add(
        responses.GET,
        url,
        body=requests.exceptions.Timeout("direct timeout"),
    )

    result = http_client.fetch_text(url, session=proxy_session)

    assert result.ok is False
    assert result.status_code == 429
    assert result.error == "HTTP 429"
    assert len(responses.calls) == 2
