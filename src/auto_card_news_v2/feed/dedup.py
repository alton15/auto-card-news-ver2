"""URL-based deduplication of feed items."""

from __future__ import annotations

from auto_card_news_v2.models import FeedItem


def deduplicate(items: list[FeedItem]) -> list[FeedItem]:
    """Remove duplicate feed items by URL, preserving order."""
    seen: set[str] = set()
    result: list[FeedItem] = []
    for item in items:
        normalized = item.url.rstrip("/").lower()
        if normalized not in seen:
            seen.add(normalized)
            result.append(item)
    return result
