"""
Tests for default runtime configuration.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import config


def test_default_network_settings_are_tuned_for_faster_failures():
    cfg = config.normalize_config({})

    assert cfg["network"]["connect_timeout_sec"] == 5
    assert cfg["network"]["read_timeout_sec"] == 10
    assert cfg["network"]["retries"] == 1
