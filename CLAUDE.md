# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Holo RSS Reader is a Python RSS/Atom feed reader packaged as an Agent Skill and local plugin wrapper. It fetches feeds concurrently, generates daily digest markdown, caches full articles, and supports importing subscriptions from GitHub Gist OPML files.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest tests

# Run a single test file
uv run pytest tests/test_fetcher.py

# Run a single test case
uv run pytest tests/test_fetcher.py::TestFetchFeed::test_fetch_rss_feed_success

# Run tests with coverage
uv run pytest --cov --cov-report=html

# Run the app from the canonical skill folder
bash skills/holo-rss-reader/scripts/rss.sh fetch|list|doctor|read|import|today|history|full

# Validate skill/plugin packaging
uv run holo-rss-validate
uv run holo-rss-sync-plugin --check
uv run holo-rss-build
```

Python 3.11+ required. Uses `uv` as the package manager.

## Architecture

Runtime skill source code lives in `skills/holo-rss-reader/scripts/`. Entry point is `skills/holo-rss-reader/scripts/main.py` which defines CLI commands (`import`, `read`, `list`, `fetch`, `today`, `history`, `full`, `doctor`, `wechat`). Packaging tooling lives in `src/holo_rss_reader_skills/`.

**Data flow for `fetch` command (the primary operation):**
`main.py` → `feeds.py` (collect feeds from Gist OPML + local feeds.json) → `fetcher.py` (concurrent fetch with ThreadPoolExecutor) → `parser.py` (extract articles) → `store.py` (update state, write digest)

**Key modules:**
- `config.py` — Loads/validates config from `$RSS_DATA_DIR/config.json` with deep merge against defaults and range clamping
- `http_client.py` — Connection-pooled HTTP with retry, size limits, encoding detection, proxy fallback. Returns `HTTPResult` dataclass
- `fetcher.py` — Feed fetching with conditional requests (ETag/Last-Modified). Returns `FeedFetchMeta` alongside articles
- `feeds.py` — Merges Gist OPML feeds with local `feeds.json`, deduplicates by URL
- `gist.py` — Extracts Gist IDs from various URL formats, fetches OPML via GitHub API, parses with defusedxml
- `parser.py` — Extracts articles from feedparser entries, truncates summaries at sentence boundaries (CJK-aware)
- `store.py` — JSON-based state management with atomic writes (temp file + rename). Tracks seen URLs, generates daily digest .md/.json, caches full articles indexed by SHA256
- `url_validator.py` — Three security modes: `loose` (scheme only), `restricted` (blocks private IPs), `allowlist` (explicit hostnames)
- `exit_codes.py` — Constants: OK=0, PARAM_ERROR=2, NETWORK_ERROR=3, PARSE_ERROR=4, STORAGE_ERROR=5

**Storage layout** (default `~/data/rss/`):
- `state.json` — Per-feed tracking: seen URLs (max 500), ETag, last_modified, consecutive failures
- `digest.md` / `digest.json` — Daily digest files
- `articles/` — Cached full articles as .md, indexed by `full_index.json`
- `config.json` — User configuration

## Key Patterns

- **Error propagation:** Functions return `(result, error_kind, error_message)` tuples. Detailed variants suffixed `*_detailed`.
- **Atomic file writes:** All state/digest writes use temp file + `os.rename`.
- **Conditional requests:** ETag/Last-Modified persisted per feed in state.json to return 304 on unchanged feeds.
- **Thread safety:** `cmd_fetch` uses locks for state and results during concurrent fetching with checkpoint saves every 20 feeds.
- **Graceful degradation:** Corrupt config/state files → backup to `.corrupt` and start fresh with defaults.

## Testing

Uses pytest with `responses` library for HTTP mocking. Fixtures in `fixtures/` (sample RSS, OPML, Gist JSON). Tests import runtime modules from `skills/holo-rss-reader/scripts/`. CI runs on Python 3.11 and 3.12.

## Environment Variables

- `RSS_DATA_DIR` — Storage root (default: `~/data/rss`)
- `RSS_CONFIG` — Config file path (alternative to `--config`)
- `RSS_PYTHON` — Python interpreter override for OpenClaw deployment
