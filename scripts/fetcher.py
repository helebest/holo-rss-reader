"""
RSS/Atom feed fetching functionality.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser

import http_client
import url_validator


class FeedFetchError(Exception):
    """Exception raised when feed fetch fails."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {url}: {reason}")


@dataclass
class FeedFetchMeta:
    status_code: Optional[int] = None
    etag: str = ""
    last_modified: str = ""
    error_kind: Optional[str] = None


def fetch_feed_detailed(
    url: str,
    *,
    session=None,
    connect_timeout_sec: int = 5,
    read_timeout_sec: int = 20,
    max_bytes: int = 2 * 1024 * 1024,
    retries: int = 3,
    conditional_headers: Optional[Dict[str, str]] = None,
    security_mode: str = "loose",
    allowlist: Optional[List[str]] = None,
) -> Tuple[Any, Optional[str], FeedFetchMeta]:
    """
    Fetch and parse an RSS/Atom feed with metadata for caching/error mapping.

    Returns:
        (feed, error_message, metadata)
    """
    validation_error = url_validator.validate_url(url, security_mode=security_mode, allowlist=allowlist)
    if validation_error:
        return (
            feedparser.parse(""),
            f"Invalid URL: {validation_error}",
            FeedFetchMeta(error_kind="validation"),
        )

    own_session = session is None
    sess = session or http_client.build_session(retries=retries)

    try:
        headers = {
            "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5"
        }
        if conditional_headers:
            headers.update(conditional_headers)

        result = http_client.fetch_text(
            url,
            session=sess,
            timeout=http_client.make_timeout(connect_timeout_sec, read_timeout_sec),
            max_bytes=max_bytes,
            headers=headers,
        )

        meta = FeedFetchMeta(
            status_code=result.status_code,
            etag=result.headers.get("etag", ""),
            last_modified=result.headers.get("last-modified", ""),
            error_kind=result.error_kind,
        )

        if not result.ok:
            return (feedparser.parse(""), result.error or "Unknown error", meta)

        if result.status_code == 304:
            return (feedparser.parse(""), None, meta)

        feed = feedparser.parse(result.text)
        if getattr(feed, "bozo", False) and not getattr(feed, "entries", []):
            bozo_exc = getattr(feed, "bozo_exception", None)
            message = f"Parse error: {bozo_exc}" if bozo_exc else "Parse error: invalid feed content"
            meta.error_kind = "parse"
            return (feed, message, meta)

        return (feed, None, meta)
    finally:
        if own_session:
            sess.close()


def fetch_feed(url: str, timeout: int = 10) -> Tuple[Any, Optional[str]]:
    """
    Backward-compatible wrapper that returns only (feed, error_message).
    """
    connect_timeout = 5 if timeout > 5 else max(1, timeout)
    feed, error, _meta = fetch_feed_detailed(
        url,
        connect_timeout_sec=connect_timeout,
        read_timeout_sec=max(1, timeout),
    )
    return feed, error


def fetch_multiple_feeds(urls: List[str], max_workers: int = 5) -> List[Tuple[Any, Optional[str]]]:
    """
    Fetch multiple feeds in parallel and preserve input order.
    """
    results: List[Tuple[Any, Optional[str]]] = [(feedparser.parse(""), "not fetched")] * len(urls)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(fetch_feed_detailed, url): idx for idx, url in enumerate(urls)}

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            feed, error, _meta = future.result()
            results[idx] = (feed, error)

    return results


def get_feed_info(feed: Any) -> Dict[str, str]:
    """
    Extract basic feed information.
    """
    return {
        "title": feed.feed.get("title", "Untitled Feed"),
        "link": feed.feed.get("link", ""),
        "description": feed.feed.get("description", ""),
        "language": feed.feed.get("language", ""),
    }


def get_entry_info(entry: Any) -> Dict[str, str]:
    """
    Extract basic entry information.
    """
    return {
        "title": entry.get("title", "Untitled"),
        "link": entry.get("link", ""),
    }
