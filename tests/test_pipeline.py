"""Tests for pipeline orchestration."""

from __future__ import annotations

from auto_card_news_v2.models import FeedItem
from auto_card_news_v2.story import build_story, sanitize_story
from auto_card_news_v2.caption import compose_caption
from auto_card_news_v2.config import load_settings


def test_full_story_to_caption_flow(sample_feed_item):
    settings = load_settings(feeds_override="https://example.com/rss")
    story = build_story(sample_feed_item)
    story = sanitize_story(story, enabled=True)
    caption = compose_caption(story, settings)

    assert len(caption) > 0
    assert "#" in caption  # has hashtags
    assert story.hook_title in caption
