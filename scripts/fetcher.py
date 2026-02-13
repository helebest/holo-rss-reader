"""
RSS/Atom feed fetching functionality.
"""
import feedparser
from typing import List, Optional, Dict, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_feed(url: str, timeout: int = 10):
    """
    Fetch and parse an RSS/Atom feed.
    
    Args:
        url: RSS/Atom feed URL
        timeout: Request timeout in seconds
        
    Returns:
        FeedParseResult object
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return feedparser.parse(response.text)
    except requests.RequestException:
        # Return empty feed on error
        return feedparser.parse("")
    except Exception:
        # Return empty feed on any error
        return feedparser.parse("")


def fetch_multiple_feeds(urls: List[str], max_workers: int = 5) -> List[Any]:
    """
    Fetch multiple feeds in parallel.
    
    Args:
        urls: List of RSS/Atom feed URLs
        max_workers: Maximum number of parallel workers
        
    Returns:
        List of FeedParseResult objects
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
