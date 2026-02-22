"""
Local storage and state management for RSS articles.
Handles: digest saving, full article caching, dedup via state.json.
"""
import json
import hashlib
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


# Default storage root
DEFAULT_RSS_DIR = os.path.expanduser("~/data/rss")


def get_rss_dir() -> Path:
    """Get RSS storage root, create if needed."""
    rss_dir = Path(os.environ.get("RSS_DATA_DIR", DEFAULT_RSS_DIR))
    rss_dir.mkdir(parents=True, exist_ok=True)
    return rss_dir


def get_state_path() -> Path:
    return get_rss_dir() / "state.json"


def load_state() -> Dict:
    """Load state.json, return empty state if not exists."""
    path = get_state_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Backup corrupt file and return empty state
            backup_path = path.with_suffix('.json.corrupt')
            path.rename(backup_path)
            return {"feeds": {}}
    return {"feeds": {}}


def save_state(state: Dict):
    """Save state.json atomically using temp file + replace."""
    path = get_state_path()
    tmp_path = path.with_suffix('.json.tmp')
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        tmp_path.replace(path)  # Atomic on POSIX
    except Exception:
        # Clean up temp file on error
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def get_seen_urls(state: Dict, feed_url: str) -> set:
    """Get set of already-seen article URLs for a feed."""
    feed_state = state.get("feeds", {}).get(feed_url, {})
    return set(feed_state.get("seen_urls", []))


def mark_seen(state: Dict, feed_url: str, article_urls: List[str]):
    """Mark article URLs as seen for a feed. Preserves order of URLs."""
    if "feeds" not in state:
        state["feeds"] = {}
    if feed_url not in state["feeds"]:
        state["feeds"][feed_url] = {"seen_urls": [], "last_fetch": None}

    # Use ordered list instead of set to preserve order
    seen_list = state["feeds"][feed_url].get("seen_urls", [])
    seen_set = set(seen_list)  # For fast lookup
    
    # Add new URLs while preserving order
    for url in article_urls:
        if url not in seen_set:
            seen_list.append(url)
            seen_set.add(url)

    # Keep max 500 URLs per feed (keep most recent)
    if len(seen_list) > 500:
        seen_list = seen_list[-500:]

    state["feeds"][feed_url]["seen_urls"] = seen_list
    state["feeds"][feed_url]["last_fetch"] = datetime.now(timezone.utc).isoformat()


def slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a filesystem-safe slug."""
    # Remove non-alphanumeric (keep Chinese chars, letters, digits)
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '-', text.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip('-')
    if not slug:
        slug = hashlib.md5(text.encode()).hexdigest()[:12]
    return slug


def get_date_dir(date_str: Optional[str] = None) -> Path:
    """Get date directory, default today."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    date_dir = get_rss_dir() / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir


def get_article_dir(date_str: Optional[str] = None) -> Path:
    """Get articles subdirectory for a date."""
    article_dir = get_date_dir(date_str) / "articles"
    article_dir.mkdir(parents=True, exist_ok=True)
    return article_dir


def article_file_path(date_str: str, feed_title: str, article_title: str) -> Path:
    """Generate file path for a full article."""
    feed_slug = slugify(feed_title, 30)
    article_slug = slugify(article_title, 50)
    filename = f"{feed_slug}--{article_slug}.md"
    return get_article_dir(date_str) / filename


def is_full_article_cached(date_str: str, feed_title: str, article_title: str) -> bool:
    """Check if full article already saved locally."""
    return article_file_path(date_str, feed_title, article_title).exists()


def save_full_article(date_str: str, feed_title: str, article: Dict, content: str):
    """Save full article content as markdown."""
    path = article_file_path(date_str, feed_title, article.get("title", "untitled"))
    md = f"# {article.get('title', 'Untitled')}\n\n"
    md += f"- **来源**: {feed_title}\n"
    md += f"- **日期**: {article.get('published', 'N/A')}\n"
    md += f"- **链接**: {article.get('link', 'N/A')}\n"
    md += f"- **抓取时间**: {datetime.now(timezone.utc).isoformat()}\n\n"
    md += "---\n\n"
    md += content
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    
    return path


def save_digest(date_str: str, articles_by_feed: Dict[str, Dict]) -> Path:
    """
    Save daily digest markdown. Merges with existing digest if present.

    articles_by_feed: {
        "feed_title": {
            "feed_url": "...",
            "articles": [{"title": ..., "link": ..., "published": ..., "summary": ...}, ...]
        }
    }
    """
    date_dir = get_date_dir(date_str)
    digest_path = date_dir / "digest.md"

    # Load existing digest data to merge
    existing = load_digest_data(date_str)
    
    # Merge: new articles append to existing feed sections
    for feed_title, feed_data in articles_by_feed.items():
        if feed_title in existing:
            # Dedup by link
            existing_links = {a.get("link") for a in existing[feed_title]["articles"]}
            for article in feed_data["articles"]:
                if article.get("link") not in existing_links:
                    existing[feed_title]["articles"].append(article)
        else:
            existing[feed_title] = feed_data

    # Render merged digest
    total_articles = sum(len(v["articles"]) for v in existing.values())

    md = f"# RSS 日报 — {date_str}\n\n"

    if total_articles == 0:
        md += "*今日无新文章。*\n"
    else:
        for feed_title, feed_data in existing.items():
            articles = feed_data["articles"]
            if not articles:
                continue

            md += f"## {feed_title}\n\n"
            for i, article in enumerate(articles, 1):
                title = article.get("title", "Untitled")
                link = article.get("link", "")
                published = article.get("published", "")[:10] if article.get("published") else ""
                summary = clean_summary(article.get("summary", ""))

                md += f"{i}. **{title}**\n"
                if published:
                    md += f"   📅 {published}"
                if link:
                    md += f" | 🔗 [{shorten_url(link)}]({link})"
                md += "\n"
                if summary:
                    short = summary[:400] + ("..." if len(summary) > 400 else "")
                    md += f"   > {short}\n"
                md += "\n"

        md += "---\n"
        feed_count = sum(1 for v in existing.values() if v["articles"])
        md += f"*共抓取 {feed_count} 个源，{total_articles} 篇新文章*\n"

    with open(digest_path, "w", encoding="utf-8") as f:
        f.write(md)

    # Also save structured data for merging
    _save_digest_data(date_str, existing)

    return digest_path


def _save_digest_data(date_str: str, articles_by_feed: Dict[str, Dict]):
    """Save structured digest data as JSON for future merging."""
    date_dir = get_date_dir(date_str)
    data_path = date_dir / "digest.json"
    
    # Convert to serializable format
    data = {}
    for feed_title, feed_data in articles_by_feed.items():
        data[feed_title] = {
            "feed_url": feed_data.get("feed_url", ""),
            "articles": feed_data["articles"],
        }
    
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_digest_data(date_str: str) -> Dict[str, Dict]:
    """Load structured digest data from JSON for merging."""
    date_dir = get_rss_dir() / date_str
    data_path = date_dir / "digest.json"
    
    if data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass
    
    return {}


def read_digest(date_str: Optional[str] = None) -> Optional[str]:
    """Read a digest file, return content or None."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    digest_path = get_rss_dir() / date_str / "digest.md"
    if digest_path.exists():
        with open(digest_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def clean_summary(text: str) -> str:
    """Strip HTML tags from summary."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def shorten_url(url: str) -> str:
    """Shorten URL for display."""
    url = re.sub(r'^https?://(www\.)?', '', url)
    if len(url) > 40:
        return url[:37] + "..."
    return url
