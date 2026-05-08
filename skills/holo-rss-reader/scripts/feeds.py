"""
Feed source management.
Supports: Gist OPML (default) + local feeds.json for custom sources.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gist


# Local feeds config location (next to state.json)
DEFAULT_RSS_DIR = os.path.expanduser("~/data/rss")


def get_feeds_config_path() -> Path:
    """Get local feeds.json path."""
    rss_dir = Path(os.environ.get("RSS_DATA_DIR", DEFAULT_RSS_DIR))
    return rss_dir / "feeds.json"


def load_local_feeds() -> List[Dict]:
    """
    Load feeds from local feeds.json.
    """
    path = get_feeds_config_path()
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("feeds", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_local_feeds(feeds: List[Dict]):
    """Save feeds to local feeds.json."""
    path = get_feeds_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {"feeds": feeds}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_local_feeds():
    """Create an empty feeds.json if it doesn't exist."""
    path = get_feeds_config_path()
    if not path.exists():
        save_local_feeds([])
        print(f"✅ 已创建本地订阅源配置: {path}")
        print("   编辑此文件添加自定义订阅源。")
    else:
        print(f"ℹ️  本地订阅源配置已存在: {path}")


def collect_all_feeds_detailed(
    gist_url: str = None,
    *,
    gist_options: Optional[Dict] = None,
) -> Tuple[List[Dict], Optional[str], Optional[str]]:
    """
    Collect feeds from all sources: Gist OPML + local feeds.json.

    Returns:
        (combined_feeds, gist_error_kind, gist_error_message)
    """
    all_feeds: List[Dict] = []
    seen_urls = set()
    gist_error_kind = None
    gist_error_message = None

    if gist_url:
        options = gist_options or {}
        gist_feeds, gist_error_kind, gist_error_message = gist.import_gist_opml_detailed(gist_url, **options)
        for feed in gist_feeds:
            url = feed.get("url", "")
            if url and url not in seen_urls:
                all_feeds.append(feed)
                seen_urls.add(url)

    local_feeds = load_local_feeds()
    for feed in local_feeds:
        url = feed.get("url", "")
        if url and url not in seen_urls:
            all_feeds.append(feed)
            seen_urls.add(url)

    return all_feeds, gist_error_kind, gist_error_message


def collect_all_feeds(gist_url: str = None) -> List[Dict]:
    """
    Backward-compatible wrapper.
    """
    feeds, _kind, _message = collect_all_feeds_detailed(gist_url)
    return feeds
