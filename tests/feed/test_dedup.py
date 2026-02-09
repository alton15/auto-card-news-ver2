"""Tests for feed deduplication."""

from __future__ import annotations

from auto_card_news_v2.feed.dedup import deduplicate
from auto_card_news_v2.models import FeedItem


def test_deduplicate_removes_exact_duplicates():
    items = [
        FeedItem(title="A", url="https://example.com/a"),
        FeedItem(title="A copy", url="https://example.com/a"),
        FeedItem(title="B", url="https://example.com/b"),
    ]
    result = deduplicate(items)
    assert len(result) == 2
    assert result[0].title == "A"
    assert result[1].title == "B"


def test_deduplicate_normalizes_trailing_slash():
    items = [
        FeedItem(title="A", url="https://example.com/a/"),
        FeedItem(title="A2", url="https://example.com/a"),
    ]
    result = deduplicate(items)
    assert len(result) == 1
