from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import parser


def test_strip_html_and_format_articles_edge_cases():
    assert parser.strip_html("") == ""
    assert parser.strip_html("<p>Hello &amp; <b>world</b></p>") == "Hello & world"
    assert parser.format_articles([]) == "No articles found."

    rendered = parser.format_articles([
        {"title": "A", "link": "https://a", "published": "2026-03-08", "summary": "S"},
        {"title": "B", "link": "", "published": "", "summary": ""},
    ])
    assert "1. A" in rendered
    assert "2. B" in rendered


def test_parse_article_without_link_or_content_uses_title_hash():
    article = parser.parse_article({"title": "Hash Me", "summary": "", "content": []})
    assert article["title"] == "Hash Me"
    assert article["link"] == ""
    assert len(article["id"]) == 32
