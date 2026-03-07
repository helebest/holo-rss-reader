"""
Tests for conditional fetch behavior (ETag/Last-Modified).
"""
from pathlib import Path
import sys

import responses

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import fetcher


@responses.activate
def test_fetch_feed_returns_not_modified_meta_on_304():
    responses.add(
        responses.GET,
        "https://example.com/feed.xml",
        body="",
        status=304,
        headers={
            "ETag": "abc123",
            "Last-Modified": "Sat, 07 Mar 2026 12:00:00 GMT",
        },
    )

    feed, error, meta = fetcher.fetch_feed_detailed(
        "https://example.com/feed.xml",
        conditional_headers={"If-None-Match": "abc123"},
    )

    assert error is None
    assert len(feed.entries) == 0
    assert meta.status_code == 304
    assert meta.etag == "abc123"
    assert meta.last_modified == "Sat, 07 Mar 2026 12:00:00 GMT"
