"""
Holo RSS Reader CLI
"""
import argparse
import sys
from pathlib import Path

import gist
import fetcher
import parser


DEFAULT_GIST_URL = "https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b"


def cmd_import_gist(gist_url: str, limit: int = 10):
    """Import and fetch feeds from a Gist OPML."""
    print(f"📥 Importing feeds from Gist...")
    print(f"   URL: {gist_url}")
    print()
    
    feeds = gist.import_gist_opml(gist_url)
    
    if not feeds:
        print("❌ No feeds found in Gist")
        return
    
    print(f"✅ Found {len(feeds)} feeds")
    print()
    
    # Fetch articles from each feed
    print(f"📰 Fetching articles from feeds (max {limit} per feed)...")
    print()
    
    for feed_info in feeds:
        print(f"--- {feed_info['title']} ---")
        
        try:
            feed = fetcher.fetch_feed(feed_info['url'])
            articles = parser.parse_articles(feed.entries, limit=limit)
            
            if articles:
                for article in articles:
                    print(f"  • {article['title']}")
                    print(f"    {article['link']}")
                    if article.get('published'):
                        print(f"    📅 {article['published'][:10]}")
                    print()
            else:
                print("  (No articles)")
                print()
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()


def cmd_read_feed(url: str, limit: int = 10):
    """Read articles from a single RSS/Atom feed."""
    print(f"📰 Fetching: {url}")
    print()
    
    feed = fetcher.fetch_feed(url)
    
    if not feed.entries:
        print("❌ No articles found")
        return
    
    feed_info = fetcher.get_feed_info(feed)
    print(f"# {feed_info['title']}")
    if feed_info.get('link'):
        print(f"🔗 {feed_info['link']}")
    print()
    
    articles = parser.parse_articles(feed.entries, limit=limit)
    print(parser.format_articles(articles))


def cmd_list_feeds(gist_url: str):
    """List all feeds from a Gist OPML."""
    print(f"📋 Listing feeds from Gist...")
    print(f"   URL: {gist_url}")
    print()
    
    feeds = gist.import_gist_opml(gist_url)
    
    if not feeds:
        print("❌ No feeds found")
        return
    
    print(f"Found {len(feeds)} feeds:\n")
    
    for i, feed in enumerate(feeds, 1):
        print(f"{i}. {feed['title']}")
        print(f"   {feed['url']}")
        if feed.get('html_url'):
            print(f"   🌐 {feed['html_url']}")
        print()


def main():
    parser_cli = argparse.ArgumentParser(
        description="Holo RSS Reader - CLI for reading RSS/Atom feeds"
    )
    
    subparsers = parser_cli.add_subparsers(dest="command", help="Commands")
    
    # Import Gist
    import_parser = subparsers.add_parser("import", help="Import feeds from Gist and fetch articles")
    import_parser.add_argument("--gist", "-g", default=DEFAULT_GIST_URL, help="Gist URL")
    import_parser.add_argument("--limit", "-l", type=int, default=3, help="Articles per feed")
    
    # Read single feed
    read_parser = subparsers.add_parser("read", help="Read articles from a feed")
    read_parser.add_argument("url", help="RSS/Atom feed URL")
    read_parser.add_argument("--limit", "-l", type=int, default=10, help="Number of articles")
    
    # List feeds
    list_parser = subparsers.add_parser("list", help="List feeds from Gist")
    list_parser.add_argument("--gist", "-g", default=DEFAULT_GIST_URL, help="Gist URL")
    
    args = parser_cli.parse_args()
    
    if args.command == "import":
        cmd_import_gist(args.gist, args.limit)
    elif args.command == "read":
        cmd_read_feed(args.url, args.limit)
    elif args.command == "list":
        cmd_list_feeds(args.gist)
    else:
        # Default: import from default Gist
        cmd_import_gist(DEFAULT_GIST_URL, limit=3)


if __name__ == "__main__":
    main()
