#!/usr/bin/env python3
"""
Holo RSS Reader - Simple RSS/Atom feed reader
"""
import feedparser
import sys
from datetime import datetime


def parse_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return date_str


def fetch_feed(url, max_items=10):
    """Fetch and parse an RSS/Atom feed"""
    feed = feedparser.parse(url)
    
    if feed.bozo:
        print(f"Warning: Feed may be malformed: {feed.bozo_exception}")
    
    return feed


def list_entries(url, max_items=10):
    """List entries from an RSS feed"""
    feed = fetch_feed(url, max_items)
    
    print(f"# {feed.feed.get('title', 'Untitled')}")
    print(f"URL: {url}")
    print(f"Entries: {len(feed.entries)}")
    print()
    
    for i, entry in enumerate(feed.entries[:max_items], 1):
        title = entry.get('title', 'No title')
        link = entry.get('link', '')
        published = entry.get('published', entry.get('updated', ''))
        
        print(f"{i}. {title}")
        if published:
            print(f"   📅 {published}")
        if link:
            print(f"   🔗 {link}")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <rss-url> [max-items]")
        print("Example: python main.py https://example.com/feed.xml 5")
        sys.exit(1)
    
    url = sys.argv[1]
    max_items = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    list_entries(url, max_items)


if __name__ == "__main__":
    main()
