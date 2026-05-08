# Holo RSS Reader

[![CI](https://github.com/helebest/holo-rss-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/helebest/holo-rss-reader/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/helebest/holo-rss-reader)](https://github.com/helebest/holo-rss-reader/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/helebest/holo-rss-reader/blob/master/LICENSE)

Production-ready RSS/Atom feed reader packaged as Agent Skills and local plugins for Codex, Claude Code, OpenClaw, and Hermes-compatible discovery flows. It supports Gist OPML import, concurrent fetching, daily digest generation, full-article caching, and WeChat Official Accounts bridging through wechat2rss.

## Features

- Parse RSS/Atom subscriptions.
- Import subscriptions from GitHub Gist OPML.
- Fetch new articles concurrently and generate a daily digest.
- Use conditional requests (`ETag` / `Last-Modified`) to reduce repeated traffic.
- Cache full-article content with `full_index.json` indexing.
- Configure network timeout, retries, payload size, and security mode.
- Run `doctor` to diagnose runtime, dependency, network, and storage issues.

## Repository Layout

This repository treats `skills/` as the canonical Agent Skills source:

| Path | Purpose |
| --- | --- |
| `skills/holo-rss-reader/` | Source-of-truth skill folder with `SKILL.md`, scripts, references, and script requirements. |
| `plugins/holo-rss-reader/` | Shared plugin wrapper for Codex, Claude Code, and OpenClaw. |
| `.agents/plugins/marketplace.json` | Codex local marketplace entry pointing to `./plugins/holo-rss-reader`. |
| `src/holo_rss_reader_skills/` | Validation, plugin sync, and release artifact build tooling. |
| `dist/` | Generated release artifacts, ignored by Git. |

Generated plugin skill copies under `plugins/holo-rss-reader/skills/` are synced from the canonical `skills/` directory and are not maintained by hand.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run coverage
uv run pytest --cov --cov-report=html

# Validate package layout
uv run holo-rss-validate
uv run holo-rss-sync-plugin --check
```

## CLI

```bash
uv run python skills/holo-rss-reader/scripts/main.py --help
uv run python skills/holo-rss-reader/scripts/main.py --config "$RSS_DATA_DIR/config.json" --help
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
    "read_timeout_sec": 10,
    "max_feed_bytes": 2097152,
    "max_article_bytes": 8388608,
    "retries": 1
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

## Distribution

Build local release artifacts:

```bash
uv run holo-rss-build
```

Release artifacts include:

| Path | Contents |
| --- | --- |
| `dist/skills/holo-rss-reader.zip` | Individual Agent Skill archive. |
| `dist/plugins/codex-holo-rss-reader-plugin.zip` | Codex plugin archive. |
| `dist/plugins/claude-holo-rss-reader-plugin.zip` | Claude Code plugin archive. |
| `dist/plugins/openclaw-holo-rss-reader-plugin.zip` | OpenClaw plugin archive. |
| `dist/site/.well-known/skills/index.json` | Well-known skills discovery index for Hermes-compatible clients. |
| `dist/site/.well-known/agent-skills/index.json` | Agent Skills discovery index. |
| `dist/checksums.txt` | SHA-256 checksums for generated artifacts. |

For local plugin testing, generate the ignored plugin skill copy:

```bash
uv run holo-rss-sync-plugin
```

Codex discovers the local plugin through `.agents/plugins/marketplace.json`. Claude Code can load the same wrapper with `claude --plugin-dir ./plugins/holo-rss-reader`. OpenClaw can load the canonical `skills/` directory directly or use the generated OpenClaw plugin archive. Hermes should consume `skills/`, generated skill zips, or the well-known discovery indexes.

For ClawHub package publishing, `plugins/holo-rss-reader/` is also an npm-packable OpenClaw plugin package. Generate the ignored skill copy first, create the ClawPack `.tgz`, then upload that artifact:

```bash
uv run holo-rss-sync-plugin
npm pack plugins/holo-rss-reader --json --ignore-scripts --pack-destination .tmp --cache .npm-cache
clawhub package publish .tmp/holo-rss-reader-<version>.tgz --family bundle-plugin --bundle-format openclaw --host-targets openclaw --source-repo helebest/holo-rss-reader --source-ref master --source-commit <commit> --dry-run
clawhub package publish .tmp/holo-rss-reader-<version>.tgz --family bundle-plugin --bundle-format openclaw --host-targets openclaw --source-repo helebest/holo-rss-reader --source-ref master --source-commit <commit>
```

When running from a skill folder:

```bash
bash skills/holo-rss-reader/scripts/rss.sh list
bash skills/holo-rss-reader/scripts/rss.sh fetch
bash skills/holo-rss-reader/scripts/rss.sh doctor
```

`rss.sh` interpreter discovery order remains:

1. `RSS_PYTHON`
2. `~/.openclaw/.venv/bin/python3`
3. `python3` (from `PATH`)

Deployable skills do not include `pyproject.toml`; Python runtime dependencies are declared in `skills/holo-rss-reader/scripts/requirements.txt`.
