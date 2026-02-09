"""Tests for story summarizer."""

from __future__ import annotations

from auto_card_news_v2.story.summarizer import build_story


def test_build_story_returns_story(sample_feed_item):
    story = build_story(sample_feed_item)
    assert story.hook_title
    assert story.what_happened
    assert len(story.key_details) > 0
    assert len(story.tags) > 0


def test_build_story_hook_title_length(sample_feed_item):
    story = build_story(sample_feed_item)
    assert len(story.hook_title) <= 120


def test_build_story_preserves_source(sample_feed_item):
    story = build_story(sample_feed_item)
    assert story.source_domain == "example.com"
    assert story.source_url == sample_feed_item.url
