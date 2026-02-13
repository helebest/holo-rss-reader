"""
Tests for article parsing functionality.
"""
import pytest
import feedparser
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import fetcher
import parser


class TestParseArticle:
    """Test parsing article information from feed entries."""
    
    def _get_feed(self):
        """Helper to get test feed."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        return feedparser.parse(rss_content.read_text())
    
    def test_parse_article_title(self):
        """Test extracting article title."""
        feed = self._get_feed()
        
        article = parser.parse_article(feed.entries[0])
        
        assert article["title"] == "Test Article 1"
    
    def test_parse_article_link(self):
        """Test extracting article link."""
        feed = self._get_feed()
        
        article = parser.parse_article(feed.entries[0])
        
        assert article["link"] == "https://example.com/article-1"
    
    def test_parse_article_published(self):
        """Test extracting article publication date."""
        feed = self._get_feed()
        
        article = parser.parse_article(feed.entries[0])
        
        assert article["published"] is not None
    
    def test_parse_article_summary(self):
        """Test extracting article summary/description."""
        feed = self._get_feed()
        
        article = parser.parse_article(feed.entries[0])
        
        assert "summary" in article
        assert "article 1" in article["summary"].lower()
    
    def test_parse_article_guid(self):
        """Test extracting article GUID."""
        feed = self._get_feed()
        
        article = parser.parse_article(feed.entries[0])
        
        assert article["id"] == "https://example.com/article-1"


class TestParseMultipleArticles:
    """Test parsing multiple articles from a feed."""
    
    def test_parse_multiple_articles(self):
        """Test parsing multiple articles."""
        feed = self._get_feed()
        
        articles = parser.parse_articles(feed.entries, limit=10)
        
        assert len(articles) == 2
        assert articles[0]["title"] == "Test Article 1"
        assert articles[1]["title"] == "Test Article 2"
    
    def test_parse_articles_with_limit(self):
        """Test limiting number of parsed articles."""
        feed = self._get_feed()
        
        articles = parser.parse_articles(feed.entries, limit=1)
        
        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article 1"
    
    def _get_feed(self):
        """Helper to get test feed."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        return feedparser.parse(rss_content.read_text())


class TestFormatArticle:
    """Test formatting article for display."""
    
    def test_format_article(self):
        """Test formatting article as string."""
        feed = self._get_feed()
        
        article = parser.parse_article(feed.entries[0])
        formatted = parser.format_article(article, index=1)
        
        assert "1." in formatted
        assert "Test Article 1" in formatted
        assert "https://example.com/article-1" in formatted
    
    def _get_feed(self):
        """Helper to get test feed."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        return feedparser.parse(rss_content.read_text())
