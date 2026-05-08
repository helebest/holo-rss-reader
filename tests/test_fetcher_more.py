from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "holo-rss-reader" / "scripts"))

import fetcher
import http_client


def test_feed_fetch_error_and_get_entry_info():
    err = fetcher.FeedFetchError("https://example.com/feed", "boom")
    assert err.url == "https://example.com/feed"
    assert err.reason == "boom"
    assert "boom" in str(err)

    assert fetcher.get_entry_info({"title": "T", "link": "https://a"}) == {"title": "T", "link": "https://a"}
    assert fetcher.get_entry_info({}) == {"title": "Untitled", "link": ""}


def test_fetch_feed_detailed_bozo_parse_error(monkeypatch):
    monkeypatch.setattr(
        fetcher.http_client,
        "fetch_text",
        lambda *args, **kwargs: http_client.HTTPResult(ok=True, status_code=200, text="<rss>broken</rss>", headers={}),
    )

    class BozoFeed:
        bozo = True
        bozo_exception = ValueError("bad xml")
        entries = []

    monkeypatch.setattr(fetcher.feedparser, "parse", lambda _text: BozoFeed())

    feed, error, meta = fetcher.fetch_feed_detailed("https://example.com/feed.xml")
    assert feed is not None
    assert "Parse error" in error
    assert meta.error_kind == "parse"

