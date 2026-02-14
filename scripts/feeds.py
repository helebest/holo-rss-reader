"""
Feed source management.
Supports: Gist OPML (default) + local feeds.json for custom sources.
"""
import json
import os
from pathlib import Path
from typing import List, Dict

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
    
    Format:
    {
        "feeds": [
            {"title": "My Blog", "url": "https://example.com/rss.xml", "html_url": "https://example.com"},
            ...
        ]
    }
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
        print(f"   编辑此文件添加自定义订阅源。")
    else:
        print(f"ℹ️  本地订阅源配置已存在: {path}")


def collect_all_feeds(gist_url: str = None) -> List[Dict]:
    """
    Collect feeds from all sources: Gist OPML + local feeds.json.
    Deduplicates by URL.
    
    Args:
        gist_url: Gist OPML URL (None to skip)
    
    Returns:
        Combined list of feed dicts with 'title', 'url', 'html_url'
    """
    all_feeds = []
    seen_urls = set()

    # 1. Load from Gist OPML
    if gist_url:
        gist_feeds = gist.import_gist_opml(gist_url)
        for feed in gist_feeds:
            url = feed.get("url", "")
            if url and url not in seen_urls:
                all_feeds.append(feed)
                seen_urls.add(url)

    # 2. Load from local feeds.json
    local_feeds = load_local_feeds()
    for feed in local_feeds:
        url = feed.get("url", "")
        if url and url not in seen_urls:
            all_feeds.append(feed)
            seen_urls.add(url)

    return all_feeds
