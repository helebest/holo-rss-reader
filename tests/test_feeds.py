from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import feeds


def test_load_local_feeds_missing_and_invalid(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    assert feeds.load_local_feeds() == []

    (tmp_path / "feeds.json").write_text("{broken", encoding="utf-8")
    assert feeds.load_local_feeds() == []


def test_save_and_init_local_feeds(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    payload = [{"title": "A", "url": "https://example.com/rss"}]

    feeds.save_local_feeds(payload)
    loaded = json.loads((tmp_path / "feeds.json").read_text(encoding="utf-8"))
    assert loaded["feeds"] == payload

    feeds.init_local_feeds()
    out = capsys.readouterr().out
    assert "已存在" in out


def test_init_local_feeds_creates_empty_file(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    feeds.init_local_feeds()
    out = capsys.readouterr().out
    assert "已创建本地订阅源配置" in out
    assert json.loads((tmp_path / "feeds.json").read_text(encoding="utf-8")) == {"feeds": []}


def test_collect_all_feeds_dedupes_gist_and_local(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    feeds.save_local_feeds([
        {"title": "Local 1", "url": "https://example.com/shared.xml"},
        {"title": "Local 2", "url": "https://example.com/local.xml"},
    ])

    monkeypatch.setattr(
        feeds.gist,
        "import_gist_opml_detailed",
        lambda *_args, **_kwargs: (
            [
                {"title": "Gist 1", "url": "https://example.com/shared.xml"},
                {"title": "Gist 2", "url": "https://example.com/gist.xml"},
            ],
            None,
            None,
        ),
    )

    merged, kind, message = feeds.collect_all_feeds_detailed("https://gist.github.com/x/y")

    assert kind is None
    assert message is None
    assert [item["url"] for item in merged] == [
        "https://example.com/shared.xml",
        "https://example.com/gist.xml",
        "https://example.com/local.xml",
    ]


def test_collect_all_feeds_returns_wrapper_result(monkeypatch):
    monkeypatch.setattr(feeds, "collect_all_feeds_detailed", lambda gist_url=None: ([{"url": "u"}], None, None))
    assert feeds.collect_all_feeds("https://gist.github.com/x/y") == [{"url": "u"}]
