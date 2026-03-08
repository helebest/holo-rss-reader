from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import store


def test_get_dirs_and_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))

    assert store.get_rss_dir() == tmp_path
    assert store.get_state_path() == tmp_path / "state.json"
    assert store.get_full_index_path() == tmp_path / "full_index.json"
    assert store.get_date_dir("2026-03-08") == tmp_path / "2026-03-08"
    assert store.get_article_dir("2026-03-08") == tmp_path / "2026-03-08" / "articles"


def test_load_state_normalizes_existing_feed_state(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    (tmp_path / "state.json").write_text(
        json.dumps({"feeds": {"https://f": {"etag": "abc", "seen_urls": "bad"}}}),
        encoding="utf-8",
    )

    state = store.load_state()

    feed_state = state["feeds"]["https://f"]
    assert feed_state["etag"] == "abc"
    assert feed_state["seen_urls"] == []
    assert feed_state["last_status"] == "never"


def test_load_state_handles_invalid_root_and_non_dict_feeds(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    path = tmp_path / "state.json"
    path.write_text("[]", encoding="utf-8")
    assert store.load_state() == {"feeds": {}}
    assert (tmp_path / "state.json.corrupt").exists()

    path.write_text(json.dumps({"feeds": []}), encoding="utf-8")
    assert store.load_state() == {"feeds": {}}


def test_save_full_index_and_lookup(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    article_path = tmp_path / "2026-03-08" / "articles" / "a.md"
    article_path.parent.mkdir(parents=True)
    article_path.write_text("content", encoding="utf-8")

    store.index_full_article("https://example.com/x", "2026-03-08", article_path)
    hit = store.lookup_full_article("https://example.com/x")

    assert hit == article_path
    assert store.load_full_index()["articles"]


def test_load_full_index_invalid_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    (tmp_path / "full_index.json").write_text("{broken", encoding="utf-8")
    assert store.load_full_index() == {"articles": {}}


def test_seen_urls_and_conditional_headers_and_meta_updates():
    state = {"feeds": {}}
    assert store.get_seen_urls(state, "https://feed") == set()
    assert store.get_feed_conditional_headers(state, "https://feed") == {}

    store.mark_seen(state, "https://feed", ["a", "a", "b"])
    headers_before = store.get_feed_conditional_headers(state, "https://feed")
    assert headers_before == {}

    store.update_feed_fetch_meta(state, "https://feed", status="error", etag="e1", last_modified="lm1", is_error=True)
    headers_after = store.get_feed_conditional_headers(state, "https://feed")
    assert headers_after == {"If-None-Match": "e1", "If-Modified-Since": "lm1"}
    assert state["feeds"]["https://feed"]["consecutive_failures"] == 1

    store.update_feed_fetch_meta(state, "https://feed", status="ok", is_error=False)
    assert state["feeds"]["https://feed"]["consecutive_failures"] == 0


def test_slugify_helpers_and_cache_checks(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))

    assert store.slugify("Hello, World!!") == "hello-world"
    assert len(store.slugify("x" * 100, max_len=10)) <= 10
    assert len(store.slugify("???")) == 12

    article_path = store.article_file_path("2026-03-08", "Feed Title", "Article Title")
    assert article_path.name.endswith(".md")
    assert store.is_full_article_cached("2026-03-08", "Feed Title", "Article Title") is False
    article_path.write_text("ok", encoding="utf-8")
    assert store.is_full_article_cached("2026-03-08", "Feed Title", "Article Title") is True


def test_save_full_article_and_digest_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    article = {
        "title": "Example Article",
        "link": "https://example.com/article",
        "published": "2026-03-08",
        "summary": "<p>Hello</p>",
    }

    article_path = store.save_full_article("2026-03-08", "Example Feed", article, "Body text")
    saved_text = article_path.read_text(encoding="utf-8")
    assert "# Example Article" in saved_text
    assert "Body text" in saved_text

    digest_path = store.save_digest(
        "2026-03-08",
        {"Example Feed": {"feed_url": "https://example.com/feed", "articles": [article]}},
    )
    # merge one new + one duplicate
    store.save_digest(
        "2026-03-08",
        {
            "Example Feed": {
                "feed_url": "https://example.com/feed",
                "articles": [article, {**article, "link": "https://example.com/article-2", "title": "Second"}],
            }
        },
    )

    digest_text = digest_path.read_text(encoding="utf-8")
    digest_json = store.load_digest_data("2026-03-08")
    assert "RSS 日报" in digest_text
    assert "Second" in digest_text
    assert len(digest_json["Example Feed"]["articles"]) == 2
    assert store.read_digest("2026-03-08") == digest_text


def test_read_digest_missing_and_text_helpers(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))

    assert store.read_digest("2026-03-08") is None
    assert store.clean_summary("<p>Hello&nbsp; <b>world</b></p>") == "Hello&nbsp; world"
    assert store.clean_summary("") == ""
    assert store.shorten_url("https://www.example.com/path") == "example.com/path"
    assert store.shorten_url("https://example.com/" + "x" * 100).endswith("...")
