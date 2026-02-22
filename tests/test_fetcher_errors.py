"""
Tests for fetcher error handling.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, 'scripts')
import fetcher


class TestFetcherErrorHandling:
    """Test that fetch errors are properly reported, not silently swallowed."""

    def test_fetch_feed_returns_error_on_network_failure(self):
        """Network failures should return error info, not silent empty feed."""
        import requests
        with patch('fetcher.requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            
            result, error = fetcher.fetch_feed("http://example.com/feed")
            
            # Should return error info, not silently swallow
            assert error is not None, "Error should be returned, not swallowed"
            assert "Network error" in error

    def test_fetch_feed_returns_error_info_on_timeout(self):
        """Timeout should return error info, not silent empty feed."""
        import requests
        with patch('fetcher.requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Timeout")
            
            result, error = fetcher.fetch_feed("http://example.com/feed", timeout=5)
            
            # Should indicate error occurred
            assert error is not None, "Error should be returned"

    def test_fetch_feed_returns_error_info_on_http_error(self):
        """HTTP errors should return error info, not silent empty feed."""
        import requests
        with patch('fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            result, error = fetcher.fetch_feed("http://example.com/feed")
            
            # Should indicate error occurred
            assert error is not None, "Error should be returned"
