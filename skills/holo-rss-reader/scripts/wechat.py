"""
WeChat public account (微信公众号) feed management via wechat2rss bridge.
"""
from typing import Dict, List, Optional, Tuple


DEFAULT_BASE_URL = "https://wechat2rss.xlab.app"
URL_TEMPLATE = "{base_url}/feed/{account_id}.xml"


def build_feed_url(account_id: str, base_url: Optional[str] = None) -> str:
    """Build a wechat2rss feed URL for the given account ID."""
    base = (base_url or DEFAULT_BASE_URL).rstrip("/")
    return URL_TEMPLATE.format(base_url=base, account_id=account_id)


def make_feed_entry(
    account_id: str,
    title: str,
    base_url: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict:
    """Create a feed dict suitable for feeds.json.

    Returns a dict with url, title, tags, and optionally headers.
    """
    entry: Dict = {
        "url": build_feed_url(account_id, base_url),
        "title": title,
        "tags": ["wechat"],
        "account_id": account_id,
    }
    if token:
        entry["headers"] = {"Authorization": f"Bearer {token}"}
    return entry


def list_wechat_feeds(feeds: List[Dict]) -> List[Dict]:
    """Filter feeds that have the 'wechat' tag."""
    return [f for f in feeds if "wechat" in (f.get("tags") or [])]


def remove_wechat_feed(
    feeds: List[Dict], identifier: str
) -> Tuple[List[Dict], Optional[Dict]]:
    """Remove a wechat feed by account_id or URL.

    Returns (updated_feeds, removed_entry). removed_entry is None if not found.
    """
    for i, feed in enumerate(feeds):
        if feed.get("account_id") == identifier or feed.get("url") == identifier:
            removed = feeds.pop(i)
            return feeds, removed
    return feeds, None
