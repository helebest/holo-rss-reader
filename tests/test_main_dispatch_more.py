from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "holo-rss-reader" / "scripts"))

import main


CFG = {
    "network": {"retries": 1, "connect_timeout_sec": 5, "read_timeout_sec": 10, "max_feed_bytes": 1024, "max_article_bytes": 1024},
    "fetch": {"workers": 4},
    "security": {"mode": "loose", "allowlist": []},
}


class DummySession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_main_dispatches_import_read_list_fetch_full_doctor(monkeypatch):
    monkeypatch.setattr(main.config_mod, "load_config", lambda _path=None: CFG)

    sessions = []
    def build_session(retries=1):
        s = DummySession()
        sessions.append(s)
        return s
    monkeypatch.setattr(main.http_client, "build_session", build_session)

    monkeypatch.setattr(main, "cmd_import_gist", lambda gist, limit, cfg, session: 21)
    monkeypatch.setattr(sys, "argv", ["rss", "import"])
    assert main.main() == 21 and sessions[-1].closed is True

    monkeypatch.setattr(main, "cmd_read_feed", lambda url, limit, cfg, session: 22)
    monkeypatch.setattr(sys, "argv", ["rss", "read", "https://feed"])
    assert main.main() == 22 and sessions[-1].closed is True

    monkeypatch.setattr(main, "cmd_list_feeds", lambda gist, cfg, session: 23)
    monkeypatch.setattr(sys, "argv", ["rss", "list"])
    assert main.main() == 23 and sessions[-1].closed is True

    monkeypatch.setattr(main, "cmd_fetch", lambda gist, limit, workers, cfg, session, **kwargs: workers)
    monkeypatch.setattr(sys, "argv", ["rss", "fetch"])
    assert main.main() == 4 and sessions[-1].closed is True

    monkeypatch.setattr(main, "cmd_full", lambda url, date, cfg, session, max_article_bytes=None: 25)
    monkeypatch.setattr(sys, "argv", ["rss", "full", "https://article"])
    assert main.main() == 25 and sessions[-1].closed is True

    monkeypatch.setattr(main, "cmd_doctor", lambda cfg, session: 26)
    monkeypatch.setattr(sys, "argv", ["rss", "doctor"])
    assert main.main() == 26 and sessions[-1].closed is True

