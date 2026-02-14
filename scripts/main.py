"""
Holo RSS Reader CLI
"""
import argparse
import sys
from datetime import datetime

import gist
import fetcher
import parser
import store
import feeds as feeds_mod


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


def cmd_fetch(gist_url: str, limit: int = 10, workers: int = 5):
    """Fetch new articles from all feeds and save daily digest.
    
    Uses concurrent fetching for speed. Saves state incrementally.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    print(f"📥 Fetching new articles (workers={workers})...")
    print(f"   Sources: Gist OPML + local feeds.json")
    print()

    all_feeds = feeds_mod.collect_all_feeds(gist_url)
    if not all_feeds:
        print("❌ No feeds found")
        return

    print(f"   Found {len(all_feeds)} feeds total")
    print()

    state = store.load_state()
    state_lock = threading.Lock()
    today = datetime.now().strftime("%Y-%m-%d")
    articles_by_feed = {}
    results_lock = threading.Lock()
    total_new = 0
    total_skipped = 0

    def process_feed(feed_info):
        """Fetch and process a single feed. Returns (title, new_count, skip_count)."""
        feed_title = feed_info["title"]
        feed_url = feed_info["url"]

        try:
            feed = fetcher.fetch_feed(feed_url)
            articles = parser.parse_articles(feed.entries, limit=limit)

            with state_lock:
                seen = store.get_seen_urls(state, feed_url)

            new_articles = []
            for a in articles:
                if a["link"] and a["link"] not in seen:
                    new_articles.append(a)

            if new_articles:
                with results_lock:
                    articles_by_feed[feed_title] = {
                        "feed_url": feed_url,
                        "articles": new_articles,
                    }
                with state_lock:
                    new_urls = [a["link"] for a in new_articles if a["link"]]
                    store.mark_seen(state, feed_url, new_urls)

                return (feed_title, len(new_articles), 0, None)
            else:
                return (feed_title, 0, len(articles), None)

        except Exception as e:
            return (feed_title, 0, 0, str(e))

    completed = 0
    save_interval = max(10, len(all_feeds) // 5)  # save ~5 times during run

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_feed = {
            executor.submit(process_feed, fi): fi for fi in all_feeds
        }

        for future in as_completed(future_to_feed):
            title, new_count, skip_count, error = future.result()
            completed += 1

            if error:
                print(f"  📡 {title}... ❌ {error}")
            elif new_count > 0:
                total_new += new_count
                print(f"  📡 {title}... ✅ {new_count} 篇新文章")
            else:
                total_skipped += skip_count
                print(f"  📡 {title}... ⏭️  无新文章 ({skip_count} 篇已读)")

            # Incremental save
            if completed % save_interval == 0:
                with state_lock:
                    store.save_state(state)
                with results_lock:
                    if articles_by_feed:
                        store.save_digest(today, articles_by_feed)

    # Final save
    store.save_state(state)

    if articles_by_feed:
        digest_path = store.save_digest(today, articles_by_feed)
        print()
        print(f"✅ 日报已保存: {digest_path}")
        print(f"   新文章: {total_new} 篇 | 跳过: {total_skipped} 篇")
    else:
        print()
        print(f"ℹ️  今日无新文章 (跳过 {total_skipped} 篇已读)")


def cmd_today():
    """Show today's digest."""
    content = store.read_digest()
    if content:
        print(content)
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"ℹ️  今日 ({today}) 还没有日报，运行 fetch 命令先抓取。")


def cmd_history(date_str: str):
    """Show digest for a specific date."""
    content = store.read_digest(date_str)
    if content:
        print(content)
    else:
        print(f"ℹ️  没有找到 {date_str} 的日报。")


def cmd_full(article_url: str, date_str: str = None):
    """Fetch and save full article content."""
    import requests
    try:
        from bs4 import BeautifulSoup
        has_bs4 = True
    except ImportError:
        has_bs4 = False

    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Try to find article info from state/digest
    feed_title = "unknown"
    article_title = store.slugify(article_url)

    # Check if already cached - scan articles dir
    article_dir = store.get_article_dir(date_str)
    for f in article_dir.iterdir():
        if f.is_file() and article_url in f.read_text(encoding="utf-8", errors="ignore")[:500]:
            print(f"✅ 全文已缓存: {f}")
            return

    print(f"📄 抓取全文: {article_url}")

    try:
        resp = requests.get(article_url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; HoloRSSReader/1.0)"
        })
        resp.raise_for_status()

        if has_bs4:
            soup = BeautifulSoup(resp.text, "lxml")
            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                article_title = title_tag.get_text(strip=True)
            # Try to find article/main content
            main = soup.find("article") or soup.find("main") or soup.find("body")
            if main:
                # Remove script/style/nav
                for tag in main.find_all(["script", "style", "nav", "header", "footer", "aside"]):
                    tag.decompose()
                content = main.get_text(separator="\n\n", strip=True)
            else:
                content = soup.get_text(separator="\n\n", strip=True)
        else:
            # Fallback: basic tag stripping
            import re
            content = re.sub(r'<[^>]+>', '', resp.text)
            content = re.sub(r'\s+', '\n', content).strip()

        article_info = {
            "title": article_title,
            "link": article_url,
            "published": date_str,
        }
        path = store.save_full_article(date_str, feed_title, article_info, content)
        print(f"✅ 全文已保存: {path}")

    except Exception as e:
        print(f"❌ 抓取失败: {e}")


def main():
    parser_cli = argparse.ArgumentParser(
        description="Holo RSS Reader - CLI for reading RSS/Atom feeds"
    )
    
    subparsers = parser_cli.add_subparsers(dest="command", help="Commands")
    
    # Import Gist (legacy)
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

    # Fetch new articles and save digest
    fetch_parser = subparsers.add_parser("fetch", help="Fetch new articles and save daily digest")
    fetch_parser.add_argument("--gist", "-g", default=DEFAULT_GIST_URL, help="Gist URL")
    fetch_parser.add_argument("--limit", "-l", type=int, default=10, help="Max articles per feed")
    fetch_parser.add_argument("--workers", "-w", type=int, default=5, help="Concurrent workers (default: 5)")

    # Show today's digest
    subparsers.add_parser("today", help="Show today's digest")

    # Show digest for a date
    history_parser = subparsers.add_parser("history", help="Show digest for a specific date")
    history_parser.add_argument("date", help="Date in YYYY-MM-DD format")

    # Fetch full article
    full_parser = subparsers.add_parser("full", help="Fetch and save full article content")
    full_parser.add_argument("url", help="Article URL")
    full_parser.add_argument("--date", "-d", default=None, help="Date folder (default: today)")

    args = parser_cli.parse_args()
    
    if args.command == "import":
        cmd_import_gist(args.gist, args.limit)
    elif args.command == "read":
        cmd_read_feed(args.url, args.limit)
    elif args.command == "list":
        cmd_list_feeds(args.gist)
    elif args.command == "fetch":
        cmd_fetch(args.gist, args.limit, args.workers)
    elif args.command == "today":
        cmd_today()
    elif args.command == "history":
        cmd_history(args.date)
    elif args.command == "full":
        cmd_full(args.url, args.date)
    else:
        parser_cli.print_help()


if __name__ == "__main__":
    main()
