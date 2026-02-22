"""
Article parsing and formatting functionality.
"""
from typing import List, Dict, Any
import hashlib
import re
import html


def strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = html.unescape(clean)
    return clean


def extract_summary(summary: str, content: str, max_len: int = 400) -> str:
    """Extract a meaningful summary from summary or content fields.

    - If the stripped summary is too short (< 80 chars) and content is
      available, fall back to content.
    - Strip HTML tags.
    - Truncate at sentence boundaries to stay within *max_len* characters.
    """
    raw = summary or ""
    text = strip_html(raw)

    if len(text) < 80 and content:
        text = strip_html(content)

    if not text:
        return ""

    if len(text) <= max_len:
        return text

    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?\u3002\uff01\uff1f])\s+", text)
    result = ""
    for s in sentences:
        candidate = (result + " " + s).strip() if result else s
        if len(candidate) > max_len:
            break
        result = candidate

    return result if result else text[:max_len] + "..."


def parse_article(entry: Any) -> Dict[str, Any]:
    """
    Parse a single feed entry into an article dictionary.

    Args:
        entry: Feed entry object

    Returns:
        Dictionary with article information
    """
    link = entry.get("link", "")
    title = entry.get("title", "Untitled")

    if link:
        article_id = link
    else:
        article_id = hashlib.md5(title.encode()).hexdigest()

    raw_summary = entry.get("summary") or entry.get("description") or ""
    raw_content = entry.get("content", [{"value": ""}])[0].get("value", "")

    return {
        "id": article_id,
        "title": title,
        "link": link,
        "published": entry.get("published") or entry.get("updated") or "",
        "summary": extract_summary(raw_summary, raw_content),
        "content": raw_content,
    }


def parse_articles(entries: List[Any], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Parse multiple feed entries into article dictionaries.

    Args:
        entries: List of feed entries
        limit: Maximum number of articles to return

    Returns:
        List of article dictionaries
    """
    articles = []

    for entry in entries[:limit]:
        article = parse_article(entry)
        articles.append(article)

    return articles


def format_article(article: Dict[str, Any], index: int = 1) -> str:
    """
    Format an article for display.

    Args:
        article: Article dictionary
        index: Article number for display

    Returns:
        Formatted string representation
    """
    lines = [
        f"{index}. {article['title']}",
    ]

    if article.get("published"):
        lines.append(f"   📅 {article['published']}")

    if article.get("link"):
        lines.append(f"   🔗 {article['link']}")

    if article.get("summary"):
        summary = article["summary"][:200]
        if len(article["summary"]) > 200:
            summary += "..."
        lines.append(f"   📝 {summary}")

    return "\n".join(lines)


def format_articles(articles: List[Dict[str, Any]]) -> str:
    """
    Format multiple articles for display.

    Args:
        articles: List of article dictionaries

    Returns:
        Formatted string with all articles
    """
    if not articles:
        return "No articles found."

    lines = []

    for i, article in enumerate(articles, 1):
        lines.append(format_article(article, i))
        lines.append("")  # Empty line between articles

    return "\n".join(lines)
