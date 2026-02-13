# SKILL.md - Holo RSS Reader

## Overview

**Name:** holo-rss-reader
**Description:** RSS/Atom feed reader for OpenClaw. Fetch and read articles from RSS feeds, with support for GitHub Gist OPML import.
**Version:** 0.1.0
**Author:** HoloBot

## Features

- Parse RSS/Atom feeds
- Fetch article list (title, date, link, summary)
- Import feeds from GitHub Gist OPML
- Customizable article limit

## Commands

### rss-list

List all RSS feeds from a Gist OPML.

**Parameters:**
- `gist_url` (optional): GitHub Gist URL containing OPML. Default: HN 2025 Popular Blogs

### rss-read

Read articles from a single RSS feed.

**Parameters:**
- `url` (required): RSS/Atom feed URL
- `limit` (optional): Number of articles to fetch. Default: 10

### rss-import

Import feeds from Gist and fetch articles.

**Parameters:**
- `gist_url` (optional): GitHub Gist URL
- `limit` (optional): Articles per feed. Default: 3

## Usage

```bash
# List feeds from Gist
python main.py list --gist "https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b"

# Read articles from a feed
python main.py read "https://news.ycombinator.com/rss" --limit 5

# Import and fetch
python main.py import --limit 2
```

## Default Feed

The skill defaults to reading from [HN 2025 Popular Blogs](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b), containing 92+ tech blogs.

## Requirements

- Python 3.11+
- feedparser
- requests

## Installation

```bash
uv sync
```
