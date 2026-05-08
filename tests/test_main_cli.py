"""
Tests for CLI parser compatibility and new options.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "holo-rss-reader" / "scripts"))

import main


def test_build_parser_accepts_fetch_extended_options():
    parser = main.build_parser()

    args = parser.parse_args(
        [
            "--config",
            "/tmp/rss-config.json",
            "fetch",
            "--gist",
            "https://gist.github.com/user/abc123",
            "--limit",
            "20",
            "--workers",
            "12",
            "--retries",
            "4",
            "--connect-timeout",
            "6",
            "--read-timeout",
            "30",
            "--max-feed-bytes",
            "123456",
        ]
    )

    assert args.command == "fetch"
    assert args.config == "/tmp/rss-config.json"
    assert args.workers == 12
    assert args.retries == 4
    assert args.connect_timeout == 6
    assert args.read_timeout == 30
    assert args.max_feed_bytes == 123456


def test_build_parser_accepts_doctor_command():
    parser = main.build_parser()
    args = parser.parse_args(["doctor"])
    assert args.command == "doctor"


def test_build_parser_accepts_full_max_article_bytes():
    parser = main.build_parser()
    args = parser.parse_args(["full", "https://example.com/a", "--max-article-bytes", "99999"])
    assert args.command == "full"
    assert args.max_article_bytes == 99999

