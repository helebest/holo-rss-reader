"""
RSS/Atom feed fetching functionality.
"""
import feedparser
from typing import List, Optional, Dict, Any, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class FeedFetchError(Exception):
    """Exception raised when feed fetch fails."""
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {url}: {reason}")


def fetch_feed(url: str, timeout: int = 10) -> Tuple[Any, Optional[str]]:
    """
    Fetch and parse an RSS/Atom feed.
    
    Args:
        url: RSS/Atom feed URL
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (FeedParseResult, error_message)
        error_message is None on success, string on failure
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return (feedparser.parse(response.text), None)
    except requests.RequestException as e:
        return (feedparser.parse(""), f"Network error: {str(e)}")
    except Exception as e:
        return (feedparser.parse(""), f"Error: {str(e)}")


def fetch_multiple_feeds(urls: List[str], max_workers: int = 5) -> List[Tuple[Any, Optional[str]]]:
    """
    Fetch multiple feeds in parallel.
    
    Args:
        urls: List of RSS/Atom feed URLs
        max_workers: Maximum number of parallel workers
        
    Returns:
        List of (FeedParseResult, error) tuples
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_feed, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
    
    return results


def get_feed_info(feed: Any) -> Dict[str, str]:
    """
    Extract basic feed information.
    
    Args:
        feed: FeedParseResult object
        
    Returns:
        Dictionary with feed metadata
    """
    return {
        'title': feed.feed.get('title', 'Untitled Feed'),
        'link': feed.feed.get('link', ''),
        'description': feed.feed.get('description', ''),
        'language': feed.feed.get('language', ''),
    }


def get_entry_info(entry: Any) -> Dict[str, str]:
    """
    Extract basic entry information.
    
    Args:
        entry: Feed entry object
        
    Returns:
        Dictionary with entry metadata
    """
    return {
        'title': entry.get('title', 'Untitled'),
        'link': entry.get('link', ''),
    }
