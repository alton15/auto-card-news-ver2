"""RSS feed fetching, parsing, and deduplication."""

from auto_card_news_v2.feed.dedup import deduplicate
from auto_card_news_v2.feed.fetcher import fetch_feed
from auto_card_news_v2.feed.history import filter_already_published
from auto_card_news_v2.feed.parser import parse_feed

__all__ = ["fetch_feed", "parse_feed", "deduplicate", "filter_already_published"]
