"""
Integration-style scale test for multi-feed fetching.
"""
from pathlib import Path
import sys

import responses

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import fetcher


@responses.activate
def test_fetch_multiple_feeds_mixed_200_sources():
    rss_content = (Path(__file__).parent.parent / "fixtures" / "sample_rss.xml").read_text()

    urls = []
    for i in range(200):
        url = f"https://example.com/feed-{i}.xml"
        urls.append(url)

        if i < 100:
            responses.add(responses.GET, url, body="", status=304)
        elif i < 180:
            responses.add(responses.GET, url, body=rss_content, status=200)
        else:
            responses.add(responses.GET, url, body="Server Error", status=500)

    results = fetcher.fetch_multiple_feeds(urls, max_workers=16)

    assert len(results) == 200

    error_count = sum(1 for _feed, error in results if error is not None)
    success_count = sum(1 for _feed, error in results if error is None)

    assert error_count == 20
    assert success_count == 180
