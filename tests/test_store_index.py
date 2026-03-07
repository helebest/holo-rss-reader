"""
Tests for full article index behavior.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import store


def test_save_full_article_updates_index(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))

    article = {
        "title": "Example Article",
        "link": "https://example.com/a1",
        "published": "2026-03-07",
    }
    path = store.save_full_article("2026-03-07", "Example Feed", article, "content")

    assert path.exists()

    hit = store.lookup_full_article("https://example.com/a1", date_str="2026-03-07")
    assert hit == path


def test_lookup_full_article_respects_date(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))

    article = {
        "title": "Date Scoped",
        "link": "https://example.com/a2",
        "published": "2026-03-07",
    }
    store.save_full_article("2026-03-07", "Example Feed", article, "content")

    miss = store.lookup_full_article("https://example.com/a2", date_str="2026-03-06")
    assert miss is None


def test_lookup_full_article_cleans_stale_index(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))

    article = {
        "title": "Stale",
        "link": "https://example.com/a3",
        "published": "2026-03-07",
    }
    path = store.save_full_article("2026-03-07", "Example Feed", article, "content")
    path.unlink()

    miss = store.lookup_full_article("https://example.com/a3", date_str="2026-03-07")
    assert miss is None

    index = store.load_full_index()
    # stale entry should be removed lazily
    entries = index.get("articles", {})
    assert len(entries) == 0
