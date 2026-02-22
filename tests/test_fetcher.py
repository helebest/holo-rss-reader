"""
Tests for RSS/Atom fetching functionality.
"""
import pytest
import responses
from pathlib import Path
import feedparser

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import fetcher


class TestFetchFeed:
    """Test RSS/Atom feed fetching."""
    
    @responses.activate
    def test_fetch_rss_feed_success(self):
        """Test successfully fetching RSS feed."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        rss_content = rss_content.read_text()
        
        responses.add(
            responses.GET,
            "https://example.com/feed.xml",
            body=rss_content,
            status=200
        )
        
        result, error = fetcher.fetch_feed("https://example.com/feed.xml")
        
        assert error is None
        assert result is not None
        assert result.feed.title == "Test RSS Feed"
        assert len(result.entries) == 5  # Fixture has 5 entries
    
    @responses.activate
    def test_fetch_feed_not_found(self):
        """Test handling 404 response."""
        responses.add(
            responses.GET,
            "https://example.com/notfound.xml",
            body="Not Found",
            status=404
        )
        
        result, error = fetcher.fetch_feed("https://example.com/notfound.xml")
        
        # 404 raises HTTPError which is caught and returns error
        assert result is not None
        assert len(result.entries) == 0
        assert error is not None  # Error info is returned
    
    @responses.activate
    def test_fetch_feed_timeout(self):
        """Test handling timeout."""
        responses.add(
            responses.GET,
            "https://example.com/timeout.xml",
            body=Exception("Connection timeout")
        )
        
        result, error = fetcher.fetch_feed("https://example.com/timeout.xml")
        
        # Should handle error gracefully
        assert result is not None
        assert error is not None  # Error info is returned


class TestFetchMultipleFeeds:
    """Test fetching multiple feeds."""
    
    @responses.activate
    def test_fetch_multiple_feeds(self):
        """Test fetching multiple feeds in parallel."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        rss_content = rss_content.read_text()
        
        responses.add(
            responses.GET,
            "https://example.com/feed1.xml",
            body=rss_content,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/feed2.xml",
            body=rss_content,
            status=200
        )
        
        urls = [
            "https://example.com/feed1.xml",
            "https://example.com/feed2.xml"
        ]
        
        # Note: fetch_multiple_feeds returns list of (feed, error) tuples now
        results = fetcher.fetch_multiple_feeds(urls)
        
        assert len(results) == 2
        # Unwrap results
        feeds = [r[0] for r in results]
        assert feeds[0].feed.title == "Test RSS Feed"
        assert feeds[1].feed.title == "Test RSS Feed"


class TestGetFeedInfo:
    """Test extracting feed information."""
    
    def test_get_feed_title(self):
        """Test extracting feed title."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        # Pass file content directly to feedparser
        feed = feedparser.parse(rss_content.read_text())
        
        info = fetcher.get_feed_info(feed)
        
        assert info["title"] == "Test RSS Feed"
        assert info["link"] == "https://example.com"
        assert info["description"] == "A test RSS feed"
