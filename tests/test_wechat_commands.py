"""Tests for wechat CLI commands in main.py."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import exit_codes
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


def test_cmd_wechat_add_success(monkeypatch, capsys, tmp_path):
    feeds_path = tmp_path / "feeds.json"
    monkeypatch.setattr(main.feeds_mod, "get_feeds_config_path", lambda: feeds_path)
    monkeypatch.setattr(
        main.fetcher,
        "fetch_feed_detailed",
        lambda *_a, **_k: (
            SimpleNamespace(entries=[{"title": "A"}]),
            None,
            SimpleNamespace(error_kind=None),
        ),
    )

    code = main.cmd_wechat_add("abc123", "TestFeed", None, None, CFG, object())
    out = capsys.readouterr().out

    assert code == exit_codes.OK
    assert "已添加微信源" in out

    data = json.loads(feeds_path.read_text())
    assert len(data["feeds"]) == 1
    assert data["feeds"][0]["account_id"] == "abc123"
    assert data["feeds"][0]["tags"] == ["wechat"]


def test_cmd_wechat_add_duplicate(monkeypatch, capsys, tmp_path):
    feeds_path = tmp_path / "feeds.json"
    feeds_path.write_text(json.dumps({
        "feeds": [{"url": "https://wechat2rss.xlab.app/feed/abc123.xml", "title": "Existing"}]
    }))
    monkeypatch.setattr(main.feeds_mod, "get_feeds_config_path", lambda: feeds_path)

    code = main.cmd_wechat_add("abc123", "TestFeed", None, None, CFG, object())
    out = capsys.readouterr().out

    assert code == exit_codes.OK
    assert "已存在" in out


def test_cmd_wechat_add_failure_network(monkeypatch, capsys, tmp_path):
    feeds_path = tmp_path / "feeds.json"
    monkeypatch.setattr(main.feeds_mod, "get_feeds_config_path", lambda: feeds_path)
    monkeypatch.setattr(
        main.fetcher,
        "fetch_feed_detailed",
        lambda *_a, **_k: (
            SimpleNamespace(entries=[]),
            "connection refused",
            SimpleNamespace(error_kind="network", status_code=None),
        ),
    )

    code = main.cmd_wechat_add("bad_id", None, None, None, CFG, object())
    out = capsys.readouterr().out

    assert code == exit_codes.NETWORK_ERROR
    assert "不可达" in out
    assert not feeds_path.exists()


def test_cmd_wechat_add_failure_not_found(monkeypatch, capsys, tmp_path):
    """When wechat2rss returns 404, show clear message about limited coverage."""
    feeds_path = tmp_path / "feeds.json"
    monkeypatch.setattr(main.feeds_mod, "get_feeds_config_path", lambda: feeds_path)
    monkeypatch.setattr(
        main.fetcher,
        "fetch_feed_detailed",
        lambda *_a, **_k: (
            SimpleNamespace(entries=[]),
            "HTTP 404",
            SimpleNamespace(error_kind="http", status_code=404),
        ),
    )

    code = main.cmd_wechat_add("unknown_id", None, None, None, CFG, object())
    out = capsys.readouterr().out

    assert code == exit_codes.NETWORK_ERROR
    assert "未收录" in out
    assert "500" in out  # mentions ~500 accounts coverage
    assert "wechat2rss.xlab.app/list/all/" in out
    assert not feeds_path.exists()


def test_cmd_wechat_add_with_token(monkeypatch, capsys, tmp_path):
    feeds_path = tmp_path / "feeds.json"
    monkeypatch.setattr(main.feeds_mod, "get_feeds_config_path", lambda: feeds_path)
    monkeypatch.setattr(
        main.fetcher,
        "fetch_feed_detailed",
        lambda *_a, **_k: (SimpleNamespace(entries=[]), None, SimpleNamespace(error_kind=None)),
    )

    code = main.cmd_wechat_add("abc123", "TestFeed", None, "mytoken", CFG, object())
    assert code == exit_codes.OK

    data = json.loads(feeds_path.read_text())
    assert data["feeds"][0]["headers"] == {"Authorization": "Bearer mytoken"}


def test_cmd_wechat_list_empty(monkeypatch, capsys):
    monkeypatch.setattr(main.feeds_mod, "load_local_feeds", lambda: [])
    code = main.cmd_wechat_list()
    assert code == exit_codes.OK
    assert "没有微信公众号" in capsys.readouterr().out


def test_cmd_wechat_list_with_feeds(monkeypatch, capsys):
    monkeypatch.setattr(main.feeds_mod, "load_local_feeds", lambda: [
        {"url": "https://example.com", "title": "Normal"},
        {"url": "https://wechat2rss.xlab.app/feed/abc.xml", "title": "WC1", "tags": ["wechat"], "account_id": "abc"},
        {"url": "https://wechat2rss.xlab.app/feed/def.xml", "title": "WC2", "tags": ["wechat"], "account_id": "def"},
    ])
    code = main.cmd_wechat_list()
    out = capsys.readouterr().out

    assert code == exit_codes.OK
    assert "WC1" in out
    assert "WC2" in out
    assert "Normal" not in out
    assert "(2)" in out


def test_cmd_wechat_remove_success(monkeypatch, capsys, tmp_path):
    feeds_path = tmp_path / "feeds.json"
    feeds_path.write_text(json.dumps({
        "feeds": [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://wechat2rss.xlab.app/feed/abc.xml", "title": "WC", "account_id": "abc", "tags": ["wechat"]},
        ]
    }))
    monkeypatch.setattr(main.feeds_mod, "get_feeds_config_path", lambda: feeds_path)

    code = main.cmd_wechat_remove("abc")
    out = capsys.readouterr().out

    assert code == exit_codes.OK
    assert "已移除" in out

    data = json.loads(feeds_path.read_text())
    assert len(data["feeds"]) == 1
    assert data["feeds"][0]["title"] == "A"


def test_cmd_wechat_remove_not_found(monkeypatch, capsys):
    monkeypatch.setattr(main.feeds_mod, "load_local_feeds", lambda: [])
    code = main.cmd_wechat_remove("nonexistent")
    assert code == exit_codes.PARAM_ERROR
    assert "未找到" in capsys.readouterr().out
