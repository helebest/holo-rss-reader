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
        
        assert len(articles) == 5
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


class TestExtractSummary:
    """Test smart summary extraction logic."""

    def test_normal_summary_unchanged(self):
        """A summary of reasonable length is returned as-is."""
        text = "This is a perfectly good summary with enough detail to be useful."
        result = parser.extract_summary(text, "")
        assert result == text

    def test_short_summary_falls_back_to_content(self):
        """When summary is too short, content is used instead."""
        short = "Too short."
        content = "This article has a very short summary but the full content field contains much more useful information."
        result = parser.extract_summary(short, content)
        assert len(result) > len(short)
        assert "full content" in result

    def test_html_stripped(self):
        """HTML tags are removed from the result."""
        html = "<p>Hello <b>world</b>.</p>"
        result = parser.extract_summary(html, "")
        assert "<" not in result
        assert "Hello world." in result

    def test_long_text_truncated_at_sentence(self):
        """Long text is truncated at a sentence boundary."""
        sentences = "First sentence. Second sentence. Third sentence. " * 10
        result = parser.extract_summary(sentences, "", max_len=100)
        assert len(result) <= 100
        assert result.endswith(".")

    def test_empty_summary_and_content(self):
        """Empty inputs return empty string."""
        assert parser.extract_summary("", "") == ""

    def test_empty_summary_uses_content(self):
        """Empty summary falls back to content."""
        content = "Content is available here. This should be used as the fallback."
        result = parser.extract_summary("", content)
        assert "Content is available" in result

    def test_max_len_respected(self):
        """Result never exceeds max_len (plus potential ellipsis)."""
        long_text = "Word " * 200
        result = parser.extract_summary(long_text, "", max_len=400)
        assert len(result) <= 403  # 400 + "..."

    def test_single_long_sentence_gets_hard_truncated(self):
        """A single sentence longer than max_len gets hard-truncated with ellipsis."""
        long_sentence = "A" * 500
        result = parser.extract_summary(long_sentence, "", max_len=400)
        assert len(result) == 403
        assert result.endswith("...")

    def test_integration_short_summary_article(self):
        """Integration: feedparser entry with short summary uses content."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        feed = feedparser.parse(rss_content.read_text())
        # "Short Summary Article" is entry index 2
        article = parser.parse_article(feed.entries[2])
        assert len(article["summary"]) > 20
        assert "software engineering" in article["summary"]

    def test_integration_html_heavy_article(self):
        """Integration: feedparser entry with heavy HTML gets clean summary."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        feed = feedparser.parse(rss_content.read_text())
        # "HTML Heavy Article" is entry index 3
        article = parser.parse_article(feed.entries[3])
        assert "<" not in article["summary"]
        assert len(article["summary"]) <= 403

    def test_integration_empty_summary_article(self):
        """Integration: feedparser entry with empty summary uses content."""
        rss_content = Path(__file__).parent.parent / "fixtures" / "sample_rss.xml"
        feed = feedparser.parse(rss_content.read_text())
        # "Empty Summary Article" is entry index 4
        article = parser.parse_article(feed.entries[4])
        assert "fallback" in article["summary"]
