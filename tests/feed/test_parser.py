"""Tests for feed parser."""

from __future__ import annotations

from auto_card_news_v2.feed.parser import parse_feed

_RSS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Breaking: Major event</title>
      <link>https://example.com/article-1</link>
      <description>Something important happened today.</description>
      <pubDate>Thu, 30 Jan 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second story</title>
      <link>https://example.com/article-2</link>
      <description>Another event occurred.</description>
    </item>
  </channel>
</rss>
"""


def test_parse_rss_xml():
    items = parse_feed(_RSS_XML, feed_url="https://example.com/rss")
    assert len(items) == 2
    assert items[0].title == "Breaking: Major event"
    assert items[0].url == "https://example.com/article-1"
    assert items[0].source_domain == "example.com"


def test_parse_rss_cleans_html():
    xml = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item>
        <title>&lt;b&gt;Bold&lt;/b&gt; title</title>
        <link>https://example.com/1</link>
        <description>&lt;p&gt;Para&lt;/p&gt;</description>
      </item>
    </channel></rss>
    """
    items = parse_feed(xml)
    assert "<" not in items[0].title
    assert "<" not in (items[0].summary or "")
