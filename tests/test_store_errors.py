"""
Tests for store.py - URL order preservation and JSON error handling.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, 'scripts')
import store


class TestStoreURLOrder:
    """Test that URL order is preserved in state."""

    def test_url_order_preserved_after_mark_seen(self):
        """URLs should be kept in order, most recent at end."""
        state = {"feeds": {}}
        urls = [f"http://example.com/{i}" for i in range(10)]
        
        # Add URLs in order
        for url in urls:
            store.mark_seen(state, "http://feed1.com", [url])
        
        # Check order is preserved (not random set order)
        saved_urls = state["feeds"]["http://feed1.com"]["seen_urls"]
        assert saved_urls == urls, f"URL order should be preserved, got {saved_urls}"

    def test_old_urls_preserved_when_truncating(self):
        """When truncating to 500, oldest URLs should be removed, not random."""
        state = {"feeds": {}}
        # Add 600 URLs
        urls = [f"http://example.com/{i}" for i in range(600)]
        
        for url in urls:
            store.mark_seen(state, "http://feed1.com", [url])
        
        saved_urls = state["feeds"]["http://feed1.com"]["seen_urls"]
        
        # Should keep the most recent 500, not random 500
        assert len(saved_urls) == 500
        assert saved_urls[0] == "http://example.com/100", "Oldest should be removed"
        assert saved_urls[-1] == "http://example.com/599", "Newest should be kept"


class TestStoreJSONDecodeError:
    """Test that corrupt state.json is handled gracefully."""

    def test_load_state_handles_corrupt_json(self):
        """Corrupt JSON should not crash, should return empty state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create corrupt state.json
            state_file = Path(tmpdir) / "state.json"
            state_file.write_text("{ invalid json }")
            
            # Mock get_state_path to use temp file
            with patch('store.get_state_path', return_value=state_file):
                result = store.load_state()
                
                # Should return empty state, not raise exception
                assert result == {"feeds": {}}

    def test_load_state_handles_truncated_json(self):
        """Truncated JSON should not crash, should return empty state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_file.write_text('{"feeds": {"url1": {"seen_urls":')  # Truncated
            
            with patch('store.get_state_path', return_value=state_file):
                result = store.load_state()
                
                assert result == {"feeds": {}}

    def test_save_state_atomic_write(self):
        """State should be saved atomically to prevent corruption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            
            with patch('store.get_state_path', return_value=state_file):
                test_state = {"feeds": {"http://test.com": {"seen_urls": ["http://a.com"]}}}
                store.save_state(test_state)
                
                # Verify file is valid JSON
                with open(state_file) as f:
                    loaded = json.load(f)
                assert loaded == test_state
