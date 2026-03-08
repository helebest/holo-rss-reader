from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import gist
import http_client


def test_find_opml_file_and_fetch_gist_detailed_validation():
    opml = gist.find_opml_file({"a.txt": {}, "b.OPML": {"content": "x"}})
    assert opml == {"content": "x"}

    data, kind, message = gist.fetch_gist_detailed("bad/id")
    assert data is None
    assert kind == "validation"
    assert "Invalid gist id" in message


def test_fetch_gist_detailed_handles_unexpected_json(monkeypatch):
    monkeypatch.setattr(
        gist.http_client,
        "fetch_json",
        lambda *args, **kwargs: http_client.HTTPResult(ok=True, status_code=200, data=[]),
    )

    data, kind, message = gist.fetch_gist_detailed("abc123")
    assert data is None
    assert kind == "parse"
    assert "Unexpected" in message


def test_import_gist_opml_detailed_error_paths(monkeypatch):
    feeds, kind, message = gist.import_gist_opml_detailed("file:///etc/passwd")
    assert feeds == []
    assert kind == "validation"

    monkeypatch.setattr(gist, "extract_gist_id", lambda _url: None)
    feeds, kind, message = gist.import_gist_opml_detailed("https://gist.github.com/user/x")
    assert kind == "validation"

    monkeypatch.setattr(gist, "extract_gist_id", lambda _url: "abc123")
    monkeypatch.setattr(gist, "fetch_gist_detailed", lambda *_a, **_k: (None, "network", "boom"))
    feeds, kind, message = gist.import_gist_opml_detailed("https://gist.github.com/user/x")
    assert kind == "network"
    assert message == "boom"

    monkeypatch.setattr(gist, "fetch_gist_detailed", lambda *_a, **_k: ({"files": {"a.txt": {}}}, None, None))
    feeds, kind, message = gist.import_gist_opml_detailed("https://gist.github.com/user/x")
    assert kind == "parse"
    assert "No OPML file" in message

    monkeypatch.setattr(gist, "fetch_gist_detailed", lambda *_a, **_k: ({"files": {"a.opml": {"content": "<opml/>"}}}, None, None))
    feeds, kind, message = gist.import_gist_opml_detailed("https://gist.github.com/user/x")
    assert kind == "parse"
    assert "No feeds found" in message


def test_import_opml_from_url_detailed_paths(monkeypatch):
    feeds, kind, message = gist.import_opml_from_url_detailed("file:///bad")
    assert kind == "validation"

    monkeypatch.setattr(
        gist.http_client,
        "fetch_text",
        lambda *args, **kwargs: http_client.HTTPResult(ok=False, error="HTTP 500", error_kind="network"),
    )
    feeds, kind, message = gist.import_opml_from_url_detailed("https://example.com/feeds.opml")
    assert feeds == []
    assert kind == "network"

    monkeypatch.setattr(
        gist.http_client,
        "fetch_text",
        lambda *args, **kwargs: http_client.HTTPResult(ok=True, status_code=200, text="<opml><body></body></opml>"),
    )
    feeds, kind, message = gist.import_opml_from_url_detailed("https://example.com/feeds.opml")
    assert kind == "parse"

    monkeypatch.setattr(
        gist.http_client,
        "fetch_text",
        lambda *args, **kwargs: http_client.HTTPResult(
            ok=True,
            status_code=200,
            text=(Path(__file__).parent.parent / "fixtures" / "sample_opml.xml").read_text(encoding="utf-8"),
        ),
    )
    feeds, kind, message = gist.import_opml_from_url_detailed("https://example.com/feeds.opml")
    assert len(feeds) == 3
    assert kind is None
    assert gist.import_opml_from_url("https://example.com/feeds.opml") == feeds
