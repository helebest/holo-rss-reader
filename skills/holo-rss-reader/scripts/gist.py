"""
Gist and OPML parsing functionality.
"""
import re
from typing import Dict, List, Optional, Tuple

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

import http_client
import url_validator


GITHUB_API_BASE = "https://api.github.com"


def extract_gist_id(url: str) -> Optional[str]:
    """
    Extract Gist ID from various Gist URL formats.
    """
    patterns = [
        r"gist\.github\.com/[a-zA-Z0-9-]+/([a-zA-Z0-9]+)",
        r"gist\.githubusercontent\.com/[a-zA-Z0-9-]+/([a-zA-Z0-9]+)",
        r"api\.github\.com/gists/([a-zA-Z0-9]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def build_gist_api_url(gist_id: str) -> str:
    """
    Build GitHub API URL for a Gist.
    """
    return f"{GITHUB_API_BASE}/gists/{gist_id}"


def fetch_gist_detailed(
    gist_id: str,
    *,
    session=None,
    connect_timeout_sec: int = 5,
    read_timeout_sec: int = 20,
    max_bytes: int = 2 * 1024 * 1024,
    retries: int = 3,
) -> Tuple[Optional[Dict], Optional[str], Optional[str]]:
    """
    Fetch Gist JSON via GitHub API.

    Returns:
        (gist_data, error_kind, error_message)
    """
    if not gist_id or not re.match(r"^[a-zA-Z0-9]+$", gist_id):
        return None, "validation", "Invalid gist id"

    own_session = session is None
    sess = session or http_client.build_session(retries=retries)
    try:
        url = build_gist_api_url(gist_id)
        result = http_client.fetch_json(
            url,
            session=sess,
            timeout=http_client.make_timeout(connect_timeout_sec, read_timeout_sec),
            max_bytes=max_bytes,
            headers={"Accept": "application/vnd.github+json"},
        )
        if not result.ok:
            return None, result.error_kind or "network", result.error or "Unknown error"
        if not isinstance(result.data, dict):
            return None, "parse", "Unexpected Gist API response"
        return result.data, None, None
    finally:
        if own_session:
            sess.close()


def fetch_gist(gist_id: str) -> Optional[Dict]:
    """
    Backward-compatible wrapper.
    """
    data, _kind, _error = fetch_gist_detailed(gist_id)
    return data


def find_opml_file(files: Dict) -> Optional[Dict]:
    """
    Find OPML file in Gist files dictionary.
    """
    for filename, file_data in files.items():
        if filename.lower().endswith(".opml"):
            return file_data

    return None


def parse_opml(opml_content: str) -> List[Dict]:
    """
    Parse OPML content and extract feed information.
    """
    feeds = []

    try:
        root = ET.fromstring(opml_content)

        for outline in root.iter("outline"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                feed = {
                    "title": outline.get("text") or outline.get("title") or "Untitled",
                    "url": xml_url,
                    "html_url": outline.get("htmlUrl", ""),
                }
                feeds.append(feed)

    except (ET.ParseError, DefusedXmlException):
        pass

    return feeds


def import_gist_opml_detailed(
    gist_url: str,
    *,
    session=None,
    connect_timeout_sec: int = 5,
    read_timeout_sec: int = 20,
    max_bytes: int = 2 * 1024 * 1024,
    retries: int = 3,
    security_mode: str = "loose",
    allowlist: Optional[List[str]] = None,
) -> Tuple[List[Dict], Optional[str], Optional[str]]:
    """
    Import feeds from a Gist containing OPML.

    Returns:
        (feeds, error_kind, error_message)
    """
    validation_error = url_validator.validate_url(gist_url, security_mode=security_mode, allowlist=allowlist)
    if validation_error:
        return [], "validation", f"Invalid gist URL: {validation_error}"

    gist_id = extract_gist_id(gist_url)
    if not gist_id:
        return [], "validation", "Unable to extract gist id from URL"

    gist_data, error_kind, error_message = fetch_gist_detailed(
        gist_id,
        session=session,
        connect_timeout_sec=connect_timeout_sec,
        read_timeout_sec=read_timeout_sec,
        max_bytes=max_bytes,
        retries=retries,
    )
    if not gist_data:
        return [], error_kind or "network", error_message or "Failed to fetch gist"

    opml_file = find_opml_file(gist_data.get("files", {}))
    if not opml_file:
        return [], "parse", "No OPML file found in gist"

    opml_content = opml_file.get("content", "")
    feeds = parse_opml(opml_content)
    if not feeds:
        return [], "parse", "No feeds found in OPML"
    return feeds, None, None


def import_gist_opml(gist_url: str) -> List[Dict]:
    """
    Backward-compatible wrapper.
    """
    feeds, _kind, _error = import_gist_opml_detailed(gist_url)
    return feeds


def import_opml_from_url_detailed(
    opml_url: str,
    *,
    session=None,
    connect_timeout_sec: int = 5,
    read_timeout_sec: int = 20,
    max_bytes: int = 2 * 1024 * 1024,
    retries: int = 3,
    security_mode: str = "loose",
    allowlist: Optional[List[str]] = None,
) -> Tuple[List[Dict], Optional[str], Optional[str]]:
    """
    Import feeds from direct OPML URL.

    Returns:
        (feeds, error_kind, error_message)
    """
    validation_error = url_validator.validate_url(opml_url, security_mode=security_mode, allowlist=allowlist)
    if validation_error:
        return [], "validation", f"Invalid OPML URL: {validation_error}"

    own_session = session is None
    sess = session or http_client.build_session(retries=retries)
    try:
        result = http_client.fetch_text(
            opml_url,
            session=sess,
            timeout=http_client.make_timeout(connect_timeout_sec, read_timeout_sec),
            max_bytes=max_bytes,
        )
        if not result.ok:
            return [], result.error_kind or "network", result.error or "Failed to download OPML"

        feeds = parse_opml(result.text)
        if not feeds:
            return [], "parse", "No feeds found in OPML"
        return feeds, None, None
    finally:
        if own_session:
            sess.close()


def import_opml_from_url(opml_url: str) -> List[Dict]:
    """
    Backward-compatible wrapper.
    """
    feeds, _kind, _error = import_opml_from_url_detailed(opml_url)
    return feeds