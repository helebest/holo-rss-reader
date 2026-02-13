"""
Article parsing and formatting functionality.
"""
from typing import List, Dict, Any
import hashlib


def parse_article(entry: Any) -> Dict[str, Any]:
    """
    Parse a single feed entry into an article dictionary.
    
    Args:
        entry: Feed entry object
        
    Returns:
        Dictionary with article information
    """
    # Generate ID from link or title if not provided
    link = entry.get('link', '')
    title = entry.get('title', 'Untitled')
    
    if link:
        article_id = link
    else:
        article_id = hashlib.md5(title.encode()).hexdigest()
    
    return {
        'id': article_id,
        'title': title,
        'link': link,
        'published': entry.get('published') or entry.get('updated') or '',
        'summary': entry.get('summary') or entry.get('description') or '',
        'content': entry.get('content', [{'value': ''}])[0].get('value', ''),
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
    
    if article.get('published'):
        lines.append(f"   📅 {article['published']}")
    
    if article.get('link'):
        lines.append(f"   🔗 {article['link']}")
    
    if article.get('summary'):
        summary = article['summary'][:200]
        if len(article['summary']) > 200:
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
