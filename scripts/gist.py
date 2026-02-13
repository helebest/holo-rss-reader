"""
Gist and OPML parsing functionality.
"""
import re
import requests
from typing import Optional, List, Dict
import xml.etree.ElementTree as ET


GITHUB_API_BASE = "https://api.github.com"


def extract_gist_id(url: str) -> Optional[str]:
    """
    Extract Gist ID from various Gist URL formats.
    
    Supported formats:
    - https://gist.github.com/username/gist_id
    - https://gist.githubusercontent.com/username/gist_id/raw/...
    - https://api.github.com/gists/gist_id
    
    Args:
        url: GitHub Gist URL
        
    Returns:
        Gist ID if found, None otherwise
    """
    patterns = [
        r'gist\.github\.com/[a-zA-Z0-9-]+/([a-zA-Z0-9]+)',
        r'gist\.githubusercontent\.com/[a-zA-Z0-9-]+/([a-zA-Z0-9]+)',
        r'api\.github\.com/gists/([a-zA-Z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def build_gist_api_url(gist_id: str) -> str:
    """
    Build GitHub API URL for a Gist.
    
    Args:
        gist_id: The Gist ID
        
    Returns:
        GitHub API URL for the Gist
    """
    return f"{GITHUB_API_BASE}/gists/{gist_id}"


def fetch_gist(gist_id: str) -> Optional[Dict]:
    """
    Fetch Gist content via GitHub API.
    
    Args:
        gist_id: The Gist ID
        
    Returns:
        Gist data as dictionary, or None if not found
    """
    url = build_gist_api_url(gist_id)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def find_opml_file(files: Dict) -> Optional[Dict]:
    """
    Find OPML file in Gist files dictionary.
    
    Args:
        files: Dictionary of files from Gist API response
        
    Returns:
        OPML file data if found, None otherwise
    """
    for filename, file_data in files.items():
        if filename.lower().endswith('.opml'):
            return file_data
    
    return None


def parse_opml(opml_content: str) -> List[Dict]:
    """
    Parse OPML content and extract feed information.
    
    Args:
        opml_content: OPML XML content as string
        
    Returns:
        List of feed dictionaries with 'title', 'url', 'html_url'
    """
    feeds = []
    
    try:
        root = ET.fromstring(opml_content)
        
        # Find all outline elements with xmlUrl attribute
        for outline in root.iter('outline'):
            xml_url = outline.get('xmlUrl')
            if xml_url:
                feed = {
                    'title': outline.get('text') or outline.get('title') or 'Untitled',
                    'url': xml_url,
                    'html_url': outline.get('htmlUrl', ''),
                }
                feeds.append(feed)
    
    except ET.ParseError:
        pass
    
    return feeds


def import_gist_opml(gist_url: str) -> List[Dict]:
    """
    Import feeds from a Gist containing OPML.
    
    Args:
        gist_url: GitHub Gist URL
        
    Returns:
        List of feed dictionaries
    """
    gist_id = extract_gist_id(gist_url)
    if not gist_id:
        return []
    
    gist_data = fetch_gist(gist_id)
    if not gist_data:
        return []
    
    opml_file = find_opml_file(gist_data.get('files', {}))
    if not opml_file:
        return []
    
    opml_content = opml_file.get('content', '')
    return parse_opml(opml_content)


def import_opml_from_url(opml_url: str) -> List[Dict]:
    """
    Import feeds from an OPML URL.
    
    Args:
        opml_url: Direct URL to OPML file
        
    Returns:
        List of feed dictionaries
    """
    try:
        response = requests.get(opml_url, timeout=10)
        response.raise_for_status()
        return parse_opml(response.text)
    except requests.RequestException:
        return []
