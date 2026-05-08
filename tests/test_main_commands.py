from pathlib import Path
import builtins
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "holo-rss-reader" / "scripts"))

import exit_codes
import http_client
import main


CFG = {
    "network": {
        "connect_timeout_sec": 5,
        "read_timeout_sec": 10,
        "max_feed_bytes": 1024,
        "max_article_bytes": 4096,
        "retries": 1,
    },
    "fetch": {"workers": 2},
    "security": {"mode": "loose", "allowlist": []},
}


def test_cmd_import_gist_success_and_error_branch(monkeypatch, capsys):
    monkeypatch.setattr(
        main.gist,
        "import_gist_opml_detailed",
        lambda *_a, **_k: (
            [
                {"title": "Good Feed", "url": "https://good/feed.xml"},
                {"title": "Bad Feed", "url": "https://bad/feed.xml"},
            ],
            None,
            None,
        ),
    )

    def fake_fetch(url, **_kwargs):
        if "bad" in url:
            return SimpleNamespace(entries=[]), "boom", SimpleNamespace(error_kind="network")
        return SimpleNamespace(entries=[{"title": "A", "link": "https://a", "published": "2026-03-08"}]), None, SimpleNamespace(error_kind=None)

    monkeypatch.setattr(main.fetcher, "fetch_feed_detailed", fake_fetch)
    monkeypatch.setattr(main.article_parser, "parse_articles", lambda entries, limit=3: entries)

    code = main.cmd_import_gist("https://gist.github.com/user/x", 3, CFG, session=object())
    out = capsys.readouterr().out

    assert code == exit_codes.NETWORK_ERROR
    assert "Found 2 feeds" in out
    assert "• A" in out
    assert "❌ Error: boom" in out


def test_cmd_import_gist_handles_empty_and_import_failure(monkeypatch, capsys):
    monkeypatch.setattr(main.gist, "import_gist_opml_detailed", lambda *_a, **_k: ([], None, None))
    assert main.cmd_import_gist("https://gist.github.com/user/x", 3, CFG, session=object()) == exit_codes.PARSE_ERROR

    monkeypatch.setattr(main.gist, "import_gist_opml_detailed", lambda *_a, **_k: ([], "network", "nope"))
    assert main.cmd_import_gist("https://gist.github.com/user/x", 3, CFG, session=object()) == exit_codes.NETWORK_ERROR
    assert "Import failed" in capsys.readouterr().out


def test_cmd_read_feed_paths(monkeypatch, capsys):
    monkeypatch.setattr(
        main.fetcher,
        "fetch_feed_detailed",
        lambda *_a, **_k: (SimpleNamespace(entries=[]), "bad", SimpleNamespace(error_kind="network")),
    )
    assert main.cmd_read_feed("https://feed", 2, CFG, object()) == exit_codes.NETWORK_ERROR

    monkeypatch.setattr(
        main.fetcher,
        "fetch_feed_detailed",
        lambda *_a, **_k: (SimpleNamespace(entries=[]), None, SimpleNamespace(error_kind=None)),
    )
    assert main.cmd_read_feed("https://feed", 2, CFG, object()) == exit_codes.PARSE_ERROR

    feed = SimpleNamespace(entries=[{"title": "X"}], feed={"title": "Feed Title", "link": "https://site"})
    monkeypatch.setattr(
        main.fetcher,
        "fetch_feed_detailed",
        lambda *_a, **_k: (feed, None, SimpleNamespace(error_kind=None)),
    )
    monkeypatch.setattr(main.fetcher, "get_feed_info", lambda _feed: {"title": "Feed Title", "link": "https://site"})
    monkeypatch.setattr(main.article_parser, "parse_articles", lambda entries, limit=2: [{"title": "X", "link": "https://x"}])
    monkeypatch.setattr(main.article_parser, "format_articles", lambda articles: "formatted articles")
    assert main.cmd_read_feed("https://feed", 2, CFG, object()) == exit_codes.OK
    assert "formatted articles" in capsys.readouterr().out


def test_cmd_list_feeds_paths(monkeypatch, capsys):
    monkeypatch.setattr(main.gist, "import_gist_opml_detailed", lambda *_a, **_k: ([], "network", "bad"))
    assert main.cmd_list_feeds("https://gist.github.com/user/x", CFG, object()) == exit_codes.NETWORK_ERROR

    monkeypatch.setattr(main.gist, "import_gist_opml_detailed", lambda *_a, **_k: ([], None, None))
    assert main.cmd_list_feeds("https://gist.github.com/user/x", CFG, object()) == exit_codes.PARSE_ERROR

    monkeypatch.setattr(
        main.gist,
        "import_gist_opml_detailed",
        lambda *_a, **_k: ([{"title": "T", "url": "https://rss", "html_url": "https://site"}], None, None),
    )
    assert main.cmd_list_feeds("https://gist.github.com/user/x", CFG, object()) == exit_codes.OK
    out = capsys.readouterr().out
    assert "Found 1 feeds" in out
    assert "🌐 https://site" in out


def test_cmd_today_and_history(monkeypatch, capsys):
    monkeypatch.setattr(main.store, "read_digest", lambda date_str=None: "digest" if date_str == "2026-03-08" or date_str is None else None)
    assert main.cmd_today() == exit_codes.OK
    assert main.cmd_history("2026-03-08") == exit_codes.OK

    monkeypatch.setattr(main.store, "read_digest", lambda date_str=None: None)
    assert main.cmd_today() == exit_codes.OK
    assert main.cmd_history("2026-03-07") == exit_codes.OK
    out = capsys.readouterr().out
    assert "还没有日报" in out
    assert "没有找到 2026-03-07 的日报" in out


def test_cmd_full_paths(monkeypatch, capsys):
    monkeypatch.setattr(main.url_validator, "validate_url", lambda *_a, **_k: "bad url")
    assert main.cmd_full("https://example.com/a", None, CFG, object()) == exit_codes.PARAM_ERROR

    monkeypatch.setattr(main.url_validator, "validate_url", lambda *_a, **_k: None)
    monkeypatch.setattr(main.store, "lookup_full_article", lambda *_a, **_k: Path("/tmp/cached.md"))
    assert main.cmd_full("https://example.com/a", "2026-03-08", CFG, object()) == exit_codes.OK

    monkeypatch.setattr(main.store, "lookup_full_article", lambda *_a, **_k: None)
    monkeypatch.setattr(main.store, "load_digest_data", lambda *_a, **_k: {})
    monkeypatch.setattr(
        main.http_client,
        "fetch_text",
        lambda *_a, **_k: http_client.HTTPResult(ok=False, error="boom", error_kind="network"),
    )
    assert main.cmd_full("https://example.com/a", "2026-03-08", CFG, object()) == exit_codes.NETWORK_ERROR


def test_cmd_full_success_without_bs4(monkeypatch, capsys):
    monkeypatch.setattr(main.url_validator, "validate_url", lambda *_a, **_k: None)
    monkeypatch.setattr(main.store, "lookup_full_article", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main.http_client,
        "fetch_text",
        lambda *_a, **_k: http_client.HTTPResult(
            ok=True,
            status_code=200,
            text="<html><title>Hello</title><body><h1>Hi</h1><p>Body</p></body></html>",
        ),
    )
    monkeypatch.setattr(main.store, "slugify", lambda text: "slugged-title")
    monkeypatch.setattr(main.store, "save_full_article", lambda *_a, **_k: Path("/tmp/full.md"))

    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "bs4":
            raise ImportError("no bs4")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert main.cmd_full("https://example.com/a", "2026-03-08", CFG, object()) == exit_codes.OK
    assert "全文已保存" in capsys.readouterr().out


def test_cmd_full_save_storage_error_with_bs4(monkeypatch):
    monkeypatch.setattr(main.url_validator, "validate_url", lambda *_a, **_k: None)
    monkeypatch.setattr(main.store, "lookup_full_article", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main.http_client,
        "fetch_text",
        lambda *_a, **_k: http_client.HTTPResult(
            ok=True,
            status_code=200,
            text="<html><title>Hello</title><body><article><p>Body</p></article></body></html>",
        ),
    )
    monkeypatch.setattr(main.store, "save_full_article", lambda *_a, **_k: (_ for _ in ()).throw(OSError("disk full")))
    assert main.cmd_full("https://example.com/a", "2026-03-08", CFG, object()) == exit_codes.STORAGE_ERROR


def test_main_dispatches_and_handles_config_error(monkeypatch):
    class DummySession:
        def close(self):
            self.closed = True

    monkeypatch.setattr(main.http_client, "build_session", lambda retries=1: DummySession())

    monkeypatch.setattr(main.config_mod, "load_config", lambda _path=None: CFG)
    monkeypatch.setattr(main, "cmd_today", lambda: 11)
    monkeypatch.setattr(sys, "argv", ["rss", "today"])
    assert main.main() == 11

    monkeypatch.setattr(main, "cmd_history", lambda date: 12)
    monkeypatch.setattr(sys, "argv", ["rss", "history", "2026-03-08"])
    assert main.main() == 12

    monkeypatch.setattr(main.config_mod, "load_config", lambda _path=None: (_ for _ in ()).throw(OSError("bad cfg")))
    monkeypatch.setattr(sys, "argv", ["rss", "today"])
    assert main.main() == exit_codes.STORAGE_ERROR


def test_cmd_full_fallback_to_feed_content(monkeypatch, capsys):
    """When HTTP fetch fails, cmd_full should fall back to digest.json content."""
    monkeypatch.setattr(main.url_validator, "validate_url", lambda *_a, **_k: None)
    monkeypatch.setattr(main.store, "lookup_full_article", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main.http_client,
        "fetch_text",
        lambda *_a, **_k: http_client.HTTPResult(ok=False, error="anti-scraping", error_kind="network"),
    )

    digest_data = {
        "TestFeed": {
            "feed_url": "https://example.com/feed.xml",
            "articles": [
                {
                    "title": "Test Article",
                    "link": "https://mp.weixin.qq.com/s/abc123",
                    "content": "<p>Full article content here</p>",
                    "summary": "Short summary",
                }
            ],
        }
    }
    monkeypatch.setattr(main.store, "load_digest_data", lambda *_a, **_k: digest_data)
    monkeypatch.setattr(main.store, "save_full_article", lambda *_a, **_k: Path("/tmp/full.md"))

    code = main.cmd_full("https://mp.weixin.qq.com/s/abc123", "2026-03-25", CFG, object())
    out = capsys.readouterr().out

    assert code == exit_codes.OK
    assert "feed 缓存的全文" in out
    assert "全文已保存" in out


def test_cmd_full_fallback_no_content_in_digest(monkeypatch, capsys):
    """When fallback finds no content in digest, it should return the original error."""
    monkeypatch.setattr(main.url_validator, "validate_url", lambda *_a, **_k: None)
    monkeypatch.setattr(main.store, "lookup_full_article", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main.http_client,
        "fetch_text",
        lambda *_a, **_k: http_client.HTTPResult(ok=False, error="timeout", error_kind="network"),
    )
    # Digest exists but article URL doesn't match
    monkeypatch.setattr(main.store, "load_digest_data", lambda *_a, **_k: {
        "SomeFeed": {"articles": [{"link": "https://other.com/x", "content": "stuff"}]}
    })

    code = main.cmd_full("https://mp.weixin.qq.com/s/notfound", "2026-03-25", CFG, object())
    assert code == exit_codes.NETWORK_ERROR

