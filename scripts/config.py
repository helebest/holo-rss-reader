"""
Runtime configuration loader.
"""
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_RSS_DIR = os.path.expanduser("~/data/rss")

DEFAULT_CONFIG: Dict[str, Any] = {
    "network": {
        "connect_timeout_sec": 5,
        "read_timeout_sec": 10,
        "max_feed_bytes": 2 * 1024 * 1024,
        "max_article_bytes": 8 * 1024 * 1024,
        "retries": 1,
    },
    "fetch": {
        "workers": 8,
    },
    "security": {
        "mode": "loose",
        "allowlist": [],
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _deep_merge(DEFAULT_CONFIG, config or {})

    network = normalized.get("network", {})
    network["connect_timeout_sec"] = _clamp_int(
        network.get("connect_timeout_sec"),
        DEFAULT_CONFIG["network"]["connect_timeout_sec"],
        1,
        60,
    )
    network["read_timeout_sec"] = _clamp_int(
        network.get("read_timeout_sec"),
        DEFAULT_CONFIG["network"]["read_timeout_sec"],
        1,
        300,
    )
    network["max_feed_bytes"] = _clamp_int(
        network.get("max_feed_bytes"),
        DEFAULT_CONFIG["network"]["max_feed_bytes"],
        64 * 1024,
        32 * 1024 * 1024,
    )
    network["max_article_bytes"] = _clamp_int(
        network.get("max_article_bytes"),
        DEFAULT_CONFIG["network"]["max_article_bytes"],
        256 * 1024,
        64 * 1024 * 1024,
    )
    network["retries"] = _clamp_int(
        network.get("retries"),
        DEFAULT_CONFIG["network"]["retries"],
        0,
        10,
    )
    normalized["network"] = network

    fetch_cfg = normalized.get("fetch", {})
    fetch_cfg["workers"] = _clamp_int(
        fetch_cfg.get("workers"),
        DEFAULT_CONFIG["fetch"]["workers"],
        1,
        64,
    )
    normalized["fetch"] = fetch_cfg

    security_cfg = normalized.get("security", {})
    mode = str(security_cfg.get("mode", "loose")).strip().lower()
    if mode not in {"loose", "restricted", "allowlist"}:
        mode = "loose"
    allowlist = security_cfg.get("allowlist", [])
    if not isinstance(allowlist, list):
        allowlist = []
    security_cfg["mode"] = mode
    security_cfg["allowlist"] = [str(item).lower().strip() for item in allowlist if str(item).strip()]
    normalized["security"] = security_cfg

    return normalized


def get_rss_data_dir() -> Path:
    rss_dir = Path(os.environ.get("RSS_DATA_DIR", DEFAULT_RSS_DIR)).expanduser()
    rss_dir.mkdir(parents=True, exist_ok=True)
    return rss_dir


def resolve_config_path(config_path: Optional[str] = None) -> Path:
    if config_path:
        return Path(config_path).expanduser()
    return get_rss_data_dir() / "config.json"


def save_config(config: Dict[str, Any], config_path: Optional[str] = None):
    path = resolve_config_path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(normalize_config(config), f, ensure_ascii=False, indent=2)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    path = resolve_config_path(config_path)
    if not path.exists():
        default_config = deepcopy(DEFAULT_CONFIG)
        save_config(default_config, str(path))
        return default_config

    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError("config root must be an object")
        return normalize_config(loaded)
    except (json.JSONDecodeError, ValueError, OSError):
        # Keep running with defaults if config is corrupt.
        return deepcopy(DEFAULT_CONFIG)
