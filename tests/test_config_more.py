from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import config


def test_load_config_creates_default_file(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))

    cfg = config.load_config()

    assert cfg["network"]["read_timeout_sec"] == 10
    assert (tmp_path / "config.json").exists()


def test_load_config_falls_back_on_corrupt_json(monkeypatch, tmp_path):
    monkeypatch.setenv("RSS_DATA_DIR", str(tmp_path))
    (tmp_path / "config.json").write_text("{oops", encoding="utf-8")

    cfg = config.load_config()

    assert cfg == config.DEFAULT_CONFIG


def test_normalize_config_clamps_and_normalizes_values():
    cfg = config.normalize_config(
        {
            "network": {
                "connect_timeout_sec": -1,
                "read_timeout_sec": 999,
                "max_feed_bytes": 1,
                "max_article_bytes": 999999999,
                "retries": 999,
            },
            "fetch": {"workers": 0},
            "security": {"mode": "weird", "allowlist": "not-a-list"},
        }
    )

    assert cfg["network"]["connect_timeout_sec"] == 1
    assert cfg["network"]["read_timeout_sec"] == 300
    assert cfg["network"]["max_feed_bytes"] == 64 * 1024
    assert cfg["network"]["max_article_bytes"] == 64 * 1024 * 1024
    assert cfg["network"]["retries"] == 10
    assert cfg["fetch"]["workers"] == 1
    assert cfg["security"]["mode"] == "loose"
    assert cfg["security"]["allowlist"] == []


def test_normalize_config_keeps_valid_security_allowlist():
    cfg = config.normalize_config({"security": {"mode": "allowlist", "allowlist": [" Example.COM ", "", 123]}})

    assert cfg["security"]["mode"] == "allowlist"
    assert cfg["security"]["allowlist"] == ["example.com", "123"]


def test_save_config_and_resolve_path(tmp_path):
    target = tmp_path / "nested" / "cfg.json"
    config.save_config({"network": {"retries": 2}}, str(target))

    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["network"]["retries"] == 2
    assert config.resolve_config_path(str(target)) == target
