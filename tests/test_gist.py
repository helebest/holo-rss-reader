"""
Tests for Gist/OPML parsing functionality.
"""
import pytest
import responses
from pathlib import Path

from holo_rss_reader import gist


class TestExtractGistId:
    """Test extracting Gist ID from various URL formats."""
    
    def test_extract_gist_id_standard_url(self):
        """Test extracting ID from standard GitHub Gist URL."""
        url = "https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b"
        result = gist.extract_gist_id(url)
        assert result == "e6d2bf860ccc367fe37ff953ba6de66b"
    
    def test_extract_gist_id_raw_url(self):
        """Test extracting ID from raw Gist URL."""
        url = "https://gist.githubusercontent.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b/raw/file.opml"
        result = gist.extract_gist_id(url)
        assert result == "e6d2bf860ccc367fe37ff953ba6de66b"
    
    def test_extract_gist_id_api_url(self):
        """Test extracting ID from GitHub API URL."""
        url = "https://api.github.com/gists/e6d2bf860ccc367fe37ff953ba6de66b"
        result = gist.extract_gist_id(url)
        assert result == "e6d2bf860ccc367fe37ff953ba6de66b"
    
    def test_extract_gist_id_invalid_url(self):
        """Test that invalid URL returns None."""
        url = "https://example.com/some/path"
        result = gist.extract_gist_id(url)
        assert result is None


class TestBuildGistApiUrl:
    """Test building GitHub API URL from Gist ID."""
    
    def test_build_api_url(self):
        """Test building API URL from Gist ID."""
        gist_id = "abc123def456"
        result = gist.build_gist_api_url(gist_id)
        assert result == "https://api.github.com/gists/abc123def456"


class TestParseOpml:
    """Test OPML parsing functionality."""
    
    def test_parse_opml_extract_feeds(self):
        """Test extracting feeds from OPML content."""
        opml_content = Path(__file__).parent.parent / "fixtures" / "sample_opml.xml"
        opml_content = opml_content.read_text()
        
        feeds = gist.parse_opml(opml_content)
        
        assert len(feeds) == 3
        assert feeds[0]["title"] == "Example Blog"
        assert feeds[0]["url"] == "https://example.com/feed.xml"
        assert feeds[1]["title"] == "Tech Blog"
        assert feeds[1]["url"] == "https://tech.example.com/rss"
    
    def test_parse_opml_empty_body(self):
        """Test parsing OPML with empty body."""
        opml_content = """<?xml version="1.0"?>
<opml version="2.0">
  <head><title>Empty</title></head>
  <body></body>
</opml>"""
        feeds = gist.parse_opml(opml_content)
        assert len(feeds) == 0


class TestFetchGistContent:
    """Test fetching Gist content via GitHub API."""
    
    @responses.activate
    def test_fetch_gist_success(self):
        """Test successfully fetching Gist content."""
        import json
        gist_id = "abc123def456"
        api_url = f"https://api.github.com/gists/{gist_id}"
        
        # Load fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_gist.json"
        fixture_content = json.loads(fixture_path.read_text())
        
        responses.add(
            responses.GET,
            api_url,
            json=fixture_content,
            status=200
        )
        
        result = gist.fetch_gist(gist_id)
        
        assert result is not None
        assert "subscriptions.opml" in result["files"]
    
    @responses.activate
    def test_fetch_gist_not_found(self):
        """Test handling non-existent Gist."""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/invalid123",
            json={"message": "Not Found"},
            status=404
        )
        
        result = gist.fetch_gist("invalid123")
        
        assert result is None


class TestImportGistOpml:
    """Test importing feeds from Gist OPML."""
    
    @responses.activate
    def test_import_gist_opml(self):
        """Test importing feeds from Gist URL."""
        import json
        gist_id = "abc123def456"
        api_url = f"https://api.github.com/gists/{gist_id}"
        
        # Load fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_gist.json"
        fixture_content = json.loads(fixture_path.read_text())
        
        responses.add(
            responses.GET,
            api_url,
            json=fixture_content,
            status=200
        )
        
        gist_url = f"https://gist.github.com/user/{gist_id}"
        feeds = gist.import_gist_opml(gist_url)
        
        assert len(feeds) == 2
        assert feeds[0]["title"] == "Blog One"
        assert feeds[0]["url"] == "https://blog1.com/feed.xml"
