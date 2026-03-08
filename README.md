# Holo RSS Reader

[![CI](https://github.com/helebest/holo-rss-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/helebest/holo-rss-reader/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/helebest/holo-rss-reader)](https://github.com/helebest/holo-rss-reader/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/helebest/holo-rss-reader)](https://github.com/helebest/holo-rss-reader)

Production-ready RSS/Atom feed reader for OpenClaw skills, with Gist OPML import, concurrent fetching, daily digest generation, and full-article caching.

## Features

- Parse RSS/Atom subscriptions.
- Import subscriptions from GitHub Gist OPML.
- Fetch new articles concurrently and generate a daily digest.
- Use conditional requests (`ETag` / `Last-Modified`) to reduce repeated traffic.
- Cache full-article content with `full_index.json` indexing.
- Configure network timeout, retries, payload size, and security mode.
- Run `doctor` to diagnose runtime, dependency, network, and storage issues.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run coverage
uv run pytest --cov --cov-report=html
```

## CLI

```bash
python3 scripts/main.py --help
python3 scripts/main.py --config "$RSS_DATA_DIR/config.json" --help
```

Commands:

- `list --gist <url>`: List feeds in a Gist.
- `read <feed-url> --limit <n>`: Read one feed.
- `import --gist <url> --limit <n>`: Import and read multiple feeds.
- `fetch --gist <url> --limit <n> --workers <n> --retries <n> --connect-timeout <sec> --read-timeout <sec> --max-feed-bytes <bytes>`
- `today`: Show today's digest.
- `history <YYYY-MM-DD>`: Show historical digest.
- `full <article-url> --date <YYYY-MM-DD> --max-article-bytes <bytes>`
- `doctor`: Run environment diagnostics.

## Configuration

Default config path: `$RSS_DATA_DIR/config.json`

```json
{
  "network": {
    "connect_timeout_sec": 5,
    "read_timeout_sec": 20,
    "max_feed_bytes": 2097152,
    "max_article_bytes": 8388608,
    "retries": 3
  },
  "fetch": {
    "workers": 8
  },
  "security": {
    "mode": "loose",
    "allowlist": []
  }
}
```

Security modes:

- `loose` (default): only require URL scheme to be `http/https`.
- `restricted`: additionally block localhost and internal/private network targets.
- `allowlist`: only allow hostnames in `allowlist`.

## Deploy to OpenClaw Skill

```bash
./openclaw_deploy_skill.sh <absolute-target-path>
```

After deployment:

```bash
bash <skill-path>/scripts/rss.sh list
bash <skill-path>/scripts/rss.sh fetch
bash <skill-path>/scripts/rss.sh doctor
```

`rss.sh` interpreter discovery order:

1. `RSS_PYTHON`
2. `~/.openclaw/.venv/bin/python3`
3. `python3` (from `PATH`)
