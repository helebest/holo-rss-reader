"""
Tests for doctor diagnostics behavior.
"""
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "holo-rss-reader" / "scripts"))

import exit_codes
import main


def test_cmd_doctor_uses_configured_max_feed_bytes(monkeypatch):
    cfg = {
        "network": {
            "connect_timeout_sec": 5,
            "read_timeout_sec": 20,
            "max_feed_bytes": 987654,
            "retries": 2,
        },
        "security": {
            "mode": "loose",
            "allowlist": [],
        },
    }

    monkeypatch.setattr(main.importlib, "import_module", lambda _name: object())
    doctor_dir = Path(".tmp") / "doctor_test_storage"
    doctor_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(main.store, "get_rss_dir", lambda: doctor_dir)

    observed = {}

    def fake_fetch_text(url, *, session, timeout, max_bytes, headers):
        observed["url"] = url
        observed["max_bytes"] = max_bytes
        return main.http_client.HTTPResult(ok=True, status_code=200, text="{}")

    def fake_fetch_feed_detailed(*_args, **_kwargs):
        return SimpleNamespace(entries=[1, 2, 3]), None, SimpleNamespace(error_kind=None)

    monkeypatch.setattr(main.http_client, "fetch_text", fake_fetch_text)
    monkeypatch.setattr(main.fetcher, "fetch_feed_detailed", fake_fetch_feed_detailed)

    code = main.cmd_doctor(cfg, session=object())

    assert code == exit_codes.OK
    assert observed["max_bytes"] == cfg["network"]["max_feed_bytes"]
