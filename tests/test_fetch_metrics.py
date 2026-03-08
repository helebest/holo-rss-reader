"""
Tests for fetch summary metrics.
"""
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import exit_codes
import main


@pytest.mark.usefixtures("tmp_path")
def test_cmd_fetch_prints_success_error_ratio_and_returns_ok(monkeypatch, capsys):
    cfg = {
        "network": {
            "connect_timeout_sec": 5,
            "read_timeout_sec": 10,
            "max_feed_bytes": 2 * 1024 * 1024,
            "retries": 1,
        },
        "fetch": {
            "workers": 2,
        },
        "security": {
            "mode": "loose",
            "allowlist": [],
        },
    }

    feeds = [
        {"title": "good-feed", "url": "https://example.com/good.xml"},
        {"title": "bad-feed", "url": "https://example.com/bad.xml"},
    ]

    monkeypatch.setattr(
        main.feeds_mod,
        "collect_all_feeds_detailed",
        lambda *_args, **_kwargs: (feeds, None, None),
    )

    def fake_fetch_feed_detailed(url, **_kwargs):
        if url.endswith("good.xml"):
            return (
                SimpleNamespace(entries=[{"title": "Article", "link": "https://example.com/a"}]),
                None,
                SimpleNamespace(status_code=200, etag="", last_modified="", error_kind=None),
            )
        return (
            SimpleNamespace(entries=[]),
            "Network error: boom",
            SimpleNamespace(status_code=None, etag="", last_modified="", error_kind="network"),
        )

    monkeypatch.setattr(main.fetcher, "fetch_feed_detailed", fake_fetch_feed_detailed)
    monkeypatch.setattr(main.article_parser, "parse_articles", lambda entries, limit=10: entries[:limit])

    monkeypatch.setattr(main.store, "load_state", lambda: {})
    monkeypatch.setattr(main.store, "get_feed_conditional_headers", lambda _state, _url: {})
    monkeypatch.setattr(main.store, "get_seen_urls", lambda _state, _url: set())
    monkeypatch.setattr(main.store, "update_feed_fetch_meta", lambda *args, **kwargs: None)
    monkeypatch.setattr(main.store, "mark_seen", lambda *args, **kwargs: None)
    monkeypatch.setattr(main.store, "save_state", lambda _state: None)
    monkeypatch.setattr(main.store, "save_digest", lambda _today, _articles_by_feed: "/tmp/digest.md")

    code = main.cmd_fetch(
        gist_url="https://gist.github.com/user/test",
        limit=10,
        workers=2,
        cfg=cfg,
        session=object(),
    )

    out = capsys.readouterr().out

    assert code == exit_codes.OK
    assert "feed_success=1/2 (50.0%) | feed_error=1/2 (50.0%)" in out
