"""
Holo RSS Reader CLI
"""
import argparse
import importlib
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Optional

import config as config_mod
import exit_codes
import feeds as feeds_mod
import fetcher
import gist
import http_client
import parser as article_parser
import store
import url_validator
import wechat


DEFAULT_GIST_URL = "https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b"


def _network_options(cfg: Dict, overrides: Optional[Dict] = None) -> Dict:
    options = {
        "connect_timeout_sec": cfg["network"]["connect_timeout_sec"],
        "read_timeout_sec": cfg["network"]["read_timeout_sec"],
        "max_bytes": cfg["network"]["max_feed_bytes"],
        "retries": cfg["network"]["retries"],
    }
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                options[key] = value
    return options


def _security_options(cfg: Dict) -> Dict:
    return {
        "security_mode": cfg["security"]["mode"],
        "allowlist": cfg["security"]["allowlist"],
    }


def _print_actionable_error(prefix: str, message: str):
    print(f"❌ {prefix}: {message}")


def cmd_import_gist(gist_url: str, limit: int, cfg: Dict, session) -> int:
    """Import and fetch feeds from a Gist OPML."""
    print("📥 Importing feeds from Gist...")
    print(f"   URL: {gist_url}")
    print()

    net_opts = _network_options(cfg)
    feeds, error_kind, error_message = gist.import_gist_opml_detailed(
        gist_url,
        session=session,
        connect_timeout_sec=net_opts["connect_timeout_sec"],
        read_timeout_sec=net_opts["read_timeout_sec"],
        max_bytes=net_opts["max_bytes"],
        retries=net_opts["retries"],
        **_security_options(cfg),
    )

    if error_message:
        _print_actionable_error("Import failed", error_message)
        return exit_codes.from_error_kind(error_kind or "network")

    if not feeds:
        print("❌ No feeds found in Gist")
        return exit_codes.PARSE_ERROR

    print(f"✅ Found {len(feeds)} feeds")
    print()

    print(f"📰 Fetching articles from feeds (max {limit} per feed)...")
    print()

    overall_code = exit_codes.OK
    for feed_info in feeds:
        print(f"--- {feed_info['title']} ---")

        feed, error, meta = fetcher.fetch_feed_detailed(
            feed_info["url"],
            session=session,
            connect_timeout_sec=net_opts["connect_timeout_sec"],
            read_timeout_sec=net_opts["read_timeout_sec"],
            max_bytes=net_opts["max_bytes"],
            retries=net_opts["retries"],
            **_security_options(cfg),
        )

        if error:
            print(f"  ❌ Error: {error}")
            overall_code = max(overall_code, exit_codes.from_error_kind(meta.error_kind or "network"))
            continue

        articles = article_parser.parse_articles(feed.entries, limit=limit)
        if articles:
            for article in articles:
                print(f"  • {article['title']}")
                print(f"    {article['link']}")
                if article.get("published"):
                    print(f"    📅 {article['published'][:10]}")
                print()
        else:
            print("  (No articles)")
            print()

    return overall_code


def cmd_read_feed(url: str, limit: int, cfg: Dict, session) -> int:
    """Read articles from a single RSS/Atom feed."""
    print(f"📰 Fetching: {url}")
    print()

    net_opts = _network_options(cfg)
    feed, error, meta = fetcher.fetch_feed_detailed(
        url,
        session=session,
        connect_timeout_sec=net_opts["connect_timeout_sec"],
        read_timeout_sec=net_opts["read_timeout_sec"],
        max_bytes=net_opts["max_bytes"],
        retries=net_opts["retries"],
        **_security_options(cfg),
    )

    if error:
        _print_actionable_error("Error fetching feed", error)
        return exit_codes.from_error_kind(meta.error_kind or "network")

    if not feed.entries:
        print("❌ No articles found")
        return exit_codes.PARSE_ERROR

    feed_info = fetcher.get_feed_info(feed)
    print(f"# {feed_info['title']}")
    if feed_info.get("link"):
        print(f"🔗 {feed_info['link']}")
    print()

    articles = article_parser.parse_articles(feed.entries, limit=limit)
    print(article_parser.format_articles(articles))
    return exit_codes.OK


def cmd_list_feeds(gist_url: str, cfg: Dict, session) -> int:
    """List all feeds from a Gist OPML."""
    print("📋 Listing feeds from Gist...")
    print(f"   URL: {gist_url}")
    print()

    net_opts = _network_options(cfg)
    feeds, error_kind, error_message = gist.import_gist_opml_detailed(
        gist_url,
        session=session,
        connect_timeout_sec=net_opts["connect_timeout_sec"],
        read_timeout_sec=net_opts["read_timeout_sec"],
        max_bytes=net_opts["max_bytes"],
        retries=net_opts["retries"],
        **_security_options(cfg),
    )

    if error_message:
        _print_actionable_error("List failed", error_message)
        return exit_codes.from_error_kind(error_kind or "network")

    if not feeds:
        print("❌ No feeds found")
        return exit_codes.PARSE_ERROR

    print(f"Found {len(feeds)} feeds:\n")

    for i, feed in enumerate(feeds, 1):
        print(f"{i}. {feed['title']}")
        print(f"   {feed['url']}")
        if feed.get("html_url"):
            print(f"   🌐 {feed['html_url']}")
        print()

    return exit_codes.OK


def cmd_fetch(
    gist_url: str,
    limit: int,
    workers: int,
    cfg: Dict,
    session,
    retries: Optional[int] = None,
    connect_timeout: Optional[int] = None,
    read_timeout: Optional[int] = None,
    max_feed_bytes: Optional[int] = None,
) -> int:
    """
    Fetch new articles from all feeds and save daily digest.
    """
    net_opts = _network_options(
        cfg,
        {
            "retries": retries,
            "connect_timeout_sec": connect_timeout,
            "read_timeout_sec": read_timeout,
            "max_bytes": max_feed_bytes,
        },
    )

    command_session = session
    own_session = False
    if retries is not None and retries != cfg["network"]["retries"]:
        command_session = http_client.build_session(retries=net_opts["retries"])
        own_session = True

    try:
        print(f"📥 Fetching new articles (workers={workers})...")
        print("   Sources: Gist OPML + local feeds.json")
        print()

        all_feeds, gist_error_kind, gist_error_message = feeds_mod.collect_all_feeds_detailed(
            gist_url,
            gist_options={
                "session": command_session,
                "connect_timeout_sec": net_opts["connect_timeout_sec"],
                "read_timeout_sec": net_opts["read_timeout_sec"],
                "max_bytes": net_opts["max_bytes"],
                "retries": net_opts["retries"],
                **_security_options(cfg),
            },
        )

        if gist_error_message:
            print(f"⚠️  Gist source unavailable: {gist_error_message}")

        if not all_feeds:
            print("❌ No feeds found")
            if gist_error_kind:
                return exit_codes.from_error_kind(gist_error_kind)
            return exit_codes.PARSE_ERROR

        print(f"   Found {len(all_feeds)} feeds total")
        print()

        try:
            state = store.load_state()
        except OSError as exc:
            _print_actionable_error("Storage error", str(exc))
            return exit_codes.STORAGE_ERROR

        state_lock = threading.Lock()
        results_lock = threading.Lock()

        today = datetime.now().strftime("%Y-%m-%d")
        articles_by_feed = {}

        total_new = 0
        total_skipped = 0
        total_304 = 0
        total_errors = 0

        start_ts = time.perf_counter()

        def process_feed(feed_info):
            feed_title = feed_info["title"]
            feed_url = feed_info["url"]
            custom_headers = feed_info.get("headers") or {}

            with state_lock:
                conditional_headers = store.get_feed_conditional_headers(state, feed_url)

            merged_headers = {**custom_headers, **conditional_headers}

            feed, error, meta = fetcher.fetch_feed_detailed(
                feed_url,
                session=command_session,
                connect_timeout_sec=net_opts["connect_timeout_sec"],
                read_timeout_sec=net_opts["read_timeout_sec"],
                max_bytes=net_opts["max_bytes"],
                retries=net_opts["retries"],
                conditional_headers=merged_headers,
                **_security_options(cfg),
            )

            if error:
                with state_lock:
                    store.update_feed_fetch_meta(
                        state,
                        feed_url,
                        status="error",
                        etag=meta.etag or None,
                        last_modified=meta.last_modified or None,
                        is_error=True,
                    )
                return {
                    "title": feed_title,
                    "status": "error",
                    "error": error,
                    "error_kind": meta.error_kind or "network",
                }

            if meta.status_code == 304:
                with state_lock:
                    store.update_feed_fetch_meta(
                        state,
                        feed_url,
                        status="not_modified",
                        etag=meta.etag or None,
                        last_modified=meta.last_modified or None,
                        is_error=False,
                    )
                return {
                    "title": feed_title,
                    "status": "not_modified",
                    "new_count": 0,
                    "skip_count": 0,
                }

            articles = article_parser.parse_articles(feed.entries, limit=limit)

            with state_lock:
                seen = store.get_seen_urls(state, feed_url)

            new_articles = [a for a in articles if a.get("link") and a["link"] not in seen]

            with state_lock:
                store.update_feed_fetch_meta(
                    state,
                    feed_url,
                    status="ok",
                    etag=meta.etag or None,
                    last_modified=meta.last_modified or None,
                    is_error=False,
                )
                if new_articles:
                    store.mark_seen(state, feed_url, [a["link"] for a in new_articles if a.get("link")])

            if new_articles:
                with results_lock:
                    articles_by_feed[feed_title] = {
                        "feed_url": feed_url,
                        "articles": new_articles,
                    }
                return {
                    "title": feed_title,
                    "status": "ok",
                    "new_count": len(new_articles),
                    "skip_count": 0,
                }

            return {
                "title": feed_title,
                "status": "ok",
                "new_count": 0,
                "skip_count": len(articles),
            }

        completed = 0
        checkpoint_interval = 20

        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(process_feed, feed_info) for feed_info in all_feeds]

                for future in as_completed(futures):
                    result = future.result()
                    completed += 1

                    if result["status"] == "error":
                        total_errors += 1
                        print(f"  📡 {result['title']}... ❌ {result['error']}")
                    elif result["status"] == "not_modified":
                        total_304 += 1
                        print(f"  📡 {result['title']}... 🧊 304 Not Modified")
                    elif result["new_count"] > 0:
                        total_new += result["new_count"]
                        print(f"  📡 {result['title']}... ✅ {result['new_count']} 篇新文章")
                    else:
                        total_skipped += result["skip_count"]
                        print(f"  📡 {result['title']}... ⏭️  无新文章 ({result['skip_count']} 篇已读)")

                    if completed % checkpoint_interval == 0:
                        with state_lock:
                            store.save_state(state)
        except OSError as exc:
            _print_actionable_error("Storage error", str(exc))
            return exit_codes.STORAGE_ERROR

        elapsed = time.perf_counter() - start_ts

        try:
            store.save_state(state)
            if articles_by_feed:
                digest_path = store.save_digest(today, articles_by_feed)
                print()
                print(f"✅ 日报已保存: {digest_path}")
            else:
                print()
                print("ℹ️  今日无新文章")
        except OSError as exc:
            _print_actionable_error("Storage error", str(exc))
            return exit_codes.STORAGE_ERROR

        success_feeds = len(all_feeds) - total_errors
        success_ratio = (success_feeds / len(all_feeds) * 100) if all_feeds else 0.0
        error_ratio = (total_errors / len(all_feeds) * 100) if all_feeds else 0.0

        print(
            f"📊 metrics: feeds_total={len(all_feeds)} new={total_new} "
            f"not_modified={total_304} skipped={total_skipped} errors={total_errors} "
            f"elapsed_sec={elapsed:.2f}"
        )
        print(
            f"📈 feed_success={success_feeds}/{len(all_feeds)} ({success_ratio:.1f}%) | "
            f"feed_error={total_errors}/{len(all_feeds)} ({error_ratio:.1f}%)"
        )

        return exit_codes.OK
    finally:
        if own_session:
            command_session.close()


def cmd_today() -> int:
    """Show today's digest."""
    content = store.read_digest()
    if content:
        print(content)
        return exit_codes.OK

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"ℹ️  今日 ({today}) 还没有日报，运行 fetch 命令先抓取。")
    return exit_codes.OK


def cmd_history(date_str: str) -> int:
    """Show digest for a specific date."""
    content = store.read_digest(date_str)
    if content:
        print(content)
        return exit_codes.OK

    print(f"ℹ️  没有找到 {date_str} 的日报。")
    return exit_codes.OK


def _lookup_feed_content(article_url: str, date_str: str):
    """Look up cached article content from digest.json.

    Returns (content, feed_title, article_title) or (None, None, None).
    """
    digest_data = store.load_digest_data(date_str)
    for feed_title, feed_data in digest_data.items():
        for article in feed_data.get("articles", []):
            if article.get("link") == article_url:
                raw_content = article.get("content", "")
                if raw_content:
                    content = article_parser.strip_html(raw_content)
                    title = article.get("title", store.slugify(article_url))
                    return content, feed_title, title
    return None, None, None


def cmd_full(
    article_url: str,
    date_str: Optional[str],
    cfg: Dict,
    session,
    max_article_bytes: Optional[int] = None,
) -> int:
    """Fetch and save full article content."""
    validation_error = url_validator.validate_url(article_url, **_security_options(cfg))
    if validation_error:
        _print_actionable_error("Invalid article URL", validation_error)
        return exit_codes.PARAM_ERROR

    try:
        from bs4 import BeautifulSoup

        has_bs4 = True
    except ImportError:
        has_bs4 = False

    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    cached = store.lookup_full_article(article_url, date_str=date_str)
    if cached:
        print(f"✅ 全文已缓存: {cached}")
        return exit_codes.OK

    print(f"📄 抓取全文: {article_url}")

    net = cfg["network"]
    max_bytes = max_article_bytes if max_article_bytes is not None else net["max_article_bytes"]

    result = http_client.fetch_text(
        article_url,
        session=session,
        timeout=http_client.make_timeout(net["connect_timeout_sec"], net["read_timeout_sec"]),
        max_bytes=max_bytes,
        headers={"Accept": "text/html,application/xhtml+xml"},
    )

    content = None
    feed_title = "unknown"
    article_title = store.slugify(article_url)

    if result.ok:
        if has_bs4:
            soup = BeautifulSoup(result.text, "lxml")
            title_tag = soup.find("title")
            if title_tag:
                article_title = title_tag.get_text(strip=True)

            main = soup.find("article") or soup.find("main") or soup.find("body")
            if main:
                for tag in main.find_all(["script", "style", "nav", "header", "footer", "aside"]):
                    tag.decompose()
                content = main.get_text(separator="\n\n", strip=True)
            else:
                content = soup.get_text(separator="\n\n", strip=True)
        else:
            import re

            content = re.sub(r"<[^>]+>", "", result.text)
            content = re.sub(r"\s+", "\n", content).strip()
    else:
        # Fallback: look up content:encoded cached in digest.json
        fallback_content, fallback_feed, fallback_title = _lookup_feed_content(article_url, date_str)
        if fallback_content:
            content = fallback_content
            feed_title = fallback_feed
            article_title = fallback_title
            print("   ℹ️  直接抓取失败，使用 feed 缓存的全文")
        else:
            _print_actionable_error("Fetch failed", result.error or "Unknown error")
            return exit_codes.from_error_kind(result.error_kind or "network")

    article_info = {
        "title": article_title,
        "link": article_url,
        "published": date_str,
    }

    try:
        path = store.save_full_article(date_str, feed_title, article_info, content)
    except OSError as exc:
        _print_actionable_error("Storage error", str(exc))
        return exit_codes.STORAGE_ERROR

    print(f"✅ 全文已保存: {path}")
    return exit_codes.OK


def cmd_doctor(cfg: Dict, session) -> int:
    """
    Run basic diagnostics for runtime and connectivity.
    """
    checks = []

    python_ok = sys.version_info >= (3, 11)
    checks.append(("python", python_ok, f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"))

    required_modules = ["feedparser", "requests", "defusedxml"]
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            checks.append((f"import:{module_name}", True, "ok"))
        except ImportError as exc:
            checks.append((f"import:{module_name}", False, str(exc)))

    try:
        rss_dir = store.get_rss_dir()
        probe = rss_dir / ".doctor_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks.append(("storage", True, str(rss_dir)))
    except OSError as exc:
        checks.append(("storage", False, str(exc)))

    net = cfg["network"]
    gist_id = gist.extract_gist_id(DEFAULT_GIST_URL) or ""
    gist_api_url = gist.build_gist_api_url(gist_id) if gist_id else "https://api.github.com"

    github_result = http_client.fetch_text(
        gist_api_url,
        session=session,
        timeout=http_client.make_timeout(net["connect_timeout_sec"], net["read_timeout_sec"]),
        max_bytes=net["max_feed_bytes"],
        headers={"Accept": "application/vnd.github+json"},
    )
    checks.append((
        "network:github",
        github_result.ok,
        f"status={github_result.status_code}" if github_result.ok else (github_result.error or "failed"),
    ))

    rss_probe_url = "https://feeds.bbci.co.uk/news/rss.xml"
    rss_result = fetcher.fetch_feed_detailed(
        rss_probe_url,
        session=session,
        connect_timeout_sec=net["connect_timeout_sec"],
        read_timeout_sec=net["read_timeout_sec"],
        max_bytes=net["max_feed_bytes"],
        retries=net["retries"],
        **_security_options(cfg),
    )
    rss_feed, rss_error, _rss_meta = rss_result
    checks.append((
        "network:rss",
        rss_error is None,
        f"entries={len(rss_feed.entries)}" if rss_error is None else rss_error,
    ))

    print("🩺 Doctor report")
    has_failure = False
    for name, ok, detail in checks:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}: {detail}")
        if not ok:
            has_failure = True

    if has_failure:
        if not python_ok:
            return exit_codes.PARAM_ERROR
        for name, ok, _detail in checks:
            if not ok and name.startswith("storage"):
                return exit_codes.STORAGE_ERROR
            if not ok and name.startswith("import"):
                return exit_codes.PARSE_ERROR
        return exit_codes.NETWORK_ERROR

    return exit_codes.OK


def cmd_wechat_add(
    account_id: str,
    title: Optional[str],
    base_url: Optional[str],
    token: Optional[str],
    cfg: Dict,
    session,
) -> int:
    """Add a WeChat public account feed via wechat2rss."""
    feed_url = wechat.build_feed_url(account_id, base_url)

    # Check for duplicates
    existing = feeds_mod.load_local_feeds()
    for f in existing:
        if f.get("url") == feed_url:
            print(f"ℹ️  已存在: {feed_url}")
            return exit_codes.OK

    # Verify feed is reachable
    print(f"🔍 验证 feed: {feed_url}")
    net_opts = _network_options(cfg)
    _feed, error, _meta = fetcher.fetch_feed_detailed(
        feed_url,
        session=session,
        connect_timeout_sec=net_opts["connect_timeout_sec"],
        read_timeout_sec=net_opts["read_timeout_sec"],
        max_bytes=net_opts["max_bytes"],
        retries=net_opts["retries"],
        **_security_options(cfg),
    )

    if error:
        if _meta.status_code in (404, 410):
            _print_actionable_error(
                "公众号未收录",
                f"wechat2rss 未收录此公众号 (account-id: {account_id})",
            )
            print("   wechat2rss 仅收录约 500 个公众号（以安全/技术类为主）。")
            print("   请到 https://wechat2rss.xlab.app/list/all/ 确认目标公众号是否在列表中。")
            print("   若未收录，暂无法通过本工具订阅该公众号。")
        else:
            _print_actionable_error("Feed 不可达", error)
            print("   未保存。请检查网络连接或 account-id 是否正确。")
        return exit_codes.NETWORK_ERROR

    feed_title = title or account_id
    entry = wechat.make_feed_entry(account_id, feed_title, base_url, token)
    existing.append(entry)
    feeds_mod.save_local_feeds(existing)
    print(f"✅ 已添加微信源: {feed_title} ({feed_url})")
    return exit_codes.OK


def cmd_wechat_list() -> int:
    """List WeChat feeds from local feeds.json."""
    all_feeds = feeds_mod.load_local_feeds()
    wechat_feeds = wechat.list_wechat_feeds(all_feeds)

    if not wechat_feeds:
        print("ℹ️  没有微信公众号订阅源。")
        print("   使用 wechat add <account-id> 添加。")
        return exit_codes.OK

    print(f"📋 微信公众号订阅源 ({len(wechat_feeds)}):\n")
    for i, feed in enumerate(wechat_feeds, 1):
        print(f"{i}. {feed.get('title', 'Untitled')}")
        print(f"   🔗 {feed.get('url', '')}")
        if feed.get("account_id"):
            print(f"   🆔 {feed['account_id']}")
        print()

    return exit_codes.OK


def cmd_wechat_remove(identifier: str) -> int:
    """Remove a WeChat feed by account-id or URL."""
    all_feeds = feeds_mod.load_local_feeds()
    updated, removed = wechat.remove_wechat_feed(all_feeds, identifier)

    if not removed:
        _print_actionable_error("未找到", f"没有匹配 '{identifier}' 的微信源")
        return exit_codes.PARAM_ERROR

    feeds_mod.save_local_feeds(updated)
    print(f"✅ 已移除: {removed.get('title', '')} ({removed.get('url', '')})")
    return exit_codes.OK


def build_parser() -> argparse.ArgumentParser:
    parser_cli = argparse.ArgumentParser(description="Holo RSS Reader - CLI for reading RSS/Atom feeds")
    parser_cli.add_argument(
        "--config",
        default=None,
        help="Path to config JSON (default: $RSS_DATA_DIR/config.json)",
    )

    subparsers = parser_cli.add_subparsers(dest="command", help="Commands", required=True)

    import_parser = subparsers.add_parser("import", help="Import feeds from Gist and fetch articles")
    import_parser.add_argument("--gist", "-g", default=DEFAULT_GIST_URL, help="Gist URL")
    import_parser.add_argument("--limit", "-l", type=int, default=3, help="Articles per feed")

    read_parser = subparsers.add_parser("read", help="Read articles from a feed")
    read_parser.add_argument("url", help="RSS/Atom feed URL")
    read_parser.add_argument("--limit", "-l", type=int, default=10, help="Number of articles")

    list_parser = subparsers.add_parser("list", help="List feeds from Gist")
    list_parser.add_argument("--gist", "-g", default=DEFAULT_GIST_URL, help="Gist URL")

    fetch_parser = subparsers.add_parser("fetch", help="Fetch new articles and save daily digest")
    fetch_parser.add_argument("--gist", "-g", default=DEFAULT_GIST_URL, help="Gist URL")
    fetch_parser.add_argument("--limit", "-l", type=int, default=10, help="Max articles per feed")
    fetch_parser.add_argument("--workers", "-w", type=int, default=None, help="Concurrent workers")
    fetch_parser.add_argument("--retries", type=int, default=None, help="HTTP retries")
    fetch_parser.add_argument("--connect-timeout", type=int, default=None, help="Connect timeout seconds")
    fetch_parser.add_argument("--read-timeout", type=int, default=None, help="Read timeout seconds")
    fetch_parser.add_argument("--max-feed-bytes", type=int, default=None, help="Max bytes per feed response")

    subparsers.add_parser("today", help="Show today's digest")

    history_parser = subparsers.add_parser("history", help="Show digest for a specific date")
    history_parser.add_argument("date", help="Date in YYYY-MM-DD format")

    full_parser = subparsers.add_parser("full", help="Fetch and save full article content")
    full_parser.add_argument("url", help="Article URL")
    full_parser.add_argument("--date", "-d", default=None, help="Date folder (default: today)")
    full_parser.add_argument("--max-article-bytes", type=int, default=None, help="Max bytes for full article")

    subparsers.add_parser("doctor", help="Run environment and connectivity diagnostics")

    wechat_parser = subparsers.add_parser("wechat", help="Manage WeChat public account feeds")
    wechat_sub = wechat_parser.add_subparsers(dest="wechat_command", help="WeChat commands")

    wechat_add = wechat_sub.add_parser("add", help="Add a WeChat feed")
    wechat_add.add_argument("account_id", help="wechat2rss account hash ID")
    wechat_add.add_argument("--title", "-t", default=None, help="Display name for the feed")
    wechat_add.add_argument("--base-url", default=None, help="wechat2rss base URL")
    wechat_add.add_argument("--token", default=None, help="Auth token (Bearer)")

    wechat_sub.add_parser("list", help="List WeChat feeds")

    wechat_rm = wechat_sub.add_parser("remove", help="Remove a WeChat feed")
    wechat_rm.add_argument("identifier", help="Account ID or feed URL")

    return parser_cli


def main() -> int:
    parser_cli = build_parser()
    args = parser_cli.parse_args()

    try:
        cfg = config_mod.load_config(args.config)
    except OSError as exc:
        _print_actionable_error("Storage error", f"Cannot load config: {exc}")
        return exit_codes.STORAGE_ERROR

    retries = cfg["network"]["retries"]
    session = http_client.build_session(retries=retries)

    try:
        if args.command == "import":
            return cmd_import_gist(args.gist, args.limit, cfg, session)
        if args.command == "read":
            return cmd_read_feed(args.url, args.limit, cfg, session)
        if args.command == "list":
            return cmd_list_feeds(args.gist, cfg, session)
        if args.command == "fetch":
            workers = args.workers if args.workers is not None else cfg["fetch"]["workers"]
            return cmd_fetch(
                args.gist,
                args.limit,
                workers,
                cfg,
                session,
                retries=args.retries,
                connect_timeout=args.connect_timeout,
                read_timeout=args.read_timeout,
                max_feed_bytes=args.max_feed_bytes,
            )
        if args.command == "today":
            return cmd_today()
        if args.command == "history":
            return cmd_history(args.date)
        if args.command == "full":
            return cmd_full(args.url, args.date, cfg, session, max_article_bytes=args.max_article_bytes)
        if args.command == "doctor":
            return cmd_doctor(cfg, session)
        if args.command == "wechat":
            if args.wechat_command == "add":
                return cmd_wechat_add(
                    args.account_id, args.title, args.base_url, args.token, cfg, session
                )
            if args.wechat_command == "list":
                return cmd_wechat_list()
            if args.wechat_command == "remove":
                return cmd_wechat_remove(args.identifier)
            parser_cli.parse_args(["wechat", "--help"])
            return exit_codes.PARAM_ERROR

        parser_cli.print_help()
        return exit_codes.PARAM_ERROR
    finally:
        session.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Avoid stack traces when piped output is closed by downstream command.
        os._exit(exit_codes.OK)
