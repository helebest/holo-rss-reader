"""Tests for wechat.py module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import wechat


def test_build_feed_url_default():
    url = wechat.build_feed_url("abc123")
    assert url == "https://wechat2rss.xlab.app/feed/abc123.xml"


def test_build_feed_url_custom_base():
    url = wechat.build_feed_url("abc123", base_url="http://localhost:4000")
    assert url == "http://localhost:4000/feed/abc123.xml"


def test_build_feed_url_strips_trailing_slash():
    url = wechat.build_feed_url("abc123", base_url="http://localhost:4000/")
    assert url == "http://localhost:4000/feed/abc123.xml"


def test_make_feed_entry_without_token():
    entry = wechat.make_feed_entry("abc123", "TestFeed")
    assert entry["url"] == "https://wechat2rss.xlab.app/feed/abc123.xml"
    assert entry["title"] == "TestFeed"
    assert entry["tags"] == ["wechat"]
    assert entry["account_id"] == "abc123"
    assert "headers" not in entry


def test_make_feed_entry_with_token():
    entry = wechat.make_feed_entry("abc123", "TestFeed", token="mytoken")
    assert entry["headers"] == {"Authorization": "Bearer mytoken"}


def test_make_feed_entry_custom_base():
    entry = wechat.make_feed_entry("abc123", "TestFeed", base_url="http://my.server")
    assert "http://my.server/feed/abc123.xml" == entry["url"]


def test_list_wechat_feeds():
    feeds = [
        {"url": "https://example.com/feed.xml", "title": "Normal"},
        {"url": "https://wechat2rss.xlab.app/feed/abc.xml", "title": "WC1", "tags": ["wechat"]},
        {"url": "https://other.com/rss", "title": "Other", "tags": ["tech"]},
        {"url": "https://wechat2rss.xlab.app/feed/def.xml", "title": "WC2", "tags": ["wechat", "ai"]},
    ]
    result = wechat.list_wechat_feeds(feeds)
    assert len(result) == 2
    assert result[0]["title"] == "WC1"
    assert result[1]["title"] == "WC2"


def test_list_wechat_feeds_empty():
    assert wechat.list_wechat_feeds([]) == []
    assert wechat.list_wechat_feeds([{"url": "x", "title": "y"}]) == []


def test_remove_wechat_feed_by_account_id():
    feeds = [
        {"url": "https://a.com", "title": "A"},
        {"url": "https://wechat2rss.xlab.app/feed/abc.xml", "title": "WC", "account_id": "abc"},
    ]
    updated, removed = wechat.remove_wechat_feed(feeds, "abc")
    assert removed["title"] == "WC"
    assert len(updated) == 1
    assert updated[0]["title"] == "A"


def test_remove_wechat_feed_by_url():
    feeds = [
        {"url": "https://wechat2rss.xlab.app/feed/abc.xml", "title": "WC", "account_id": "abc"},
    ]
    updated, removed = wechat.remove_wechat_feed(feeds, "https://wechat2rss.xlab.app/feed/abc.xml")
    assert removed is not None
    assert len(updated) == 0


def test_remove_wechat_feed_not_found():
    feeds = [{"url": "https://a.com", "title": "A"}]
    updated, removed = wechat.remove_wechat_feed(feeds, "nonexistent")
    assert removed is None
    assert len(updated) == 1
