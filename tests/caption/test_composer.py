"""Tests for caption composer, including Threads 500-char limit."""

from __future__ import annotations

from pathlib import Path

from auto_card_news_v2.caption.composer import compose_caption
from auto_card_news_v2.config import Settings
from auto_card_news_v2.models import Story

_SETTINGS = Settings(
    rss_feeds=("https://example.com/rss",),
    output_dir=Path("."),
    safety_enabled=False,
    max_items=10,
    num_cards=6,
    brand_name="TestBrand",
    brand_handle="@test",
)


def _make_story(
    *,
    hook_title: str = "Short title",
    key_details: tuple[str, ...] = ("Detail one.", "Detail two.", "Detail three."),
    tags: tuple[str, ...] = ("news", "test"),
    source_domain: str = "example.com",
) -> Story:
    return Story(
        hook_title=hook_title,
        what_happened="Something happened.",
        where_when="Seoul, today.",
        impact="Big impact.",
        key_details=key_details,
        what_next="More to come.",
        tags=tags,
        source_domain=source_domain,
    )


def test_compose_caption_returns_string():
    story = _make_story()
    caption = compose_caption(story, _SETTINGS)
    assert isinstance(caption, str)
    assert len(caption) > 0


def test_compose_caption_within_500_chars():
    """Caption must never exceed Threads 500-char limit."""
    story = _make_story()
    caption = compose_caption(story, _SETTINGS)
    assert len(caption) <= 500, f"Caption is {len(caption)} chars, max 500"


def test_compose_caption_long_details_within_limit():
    """Even with very long key details, caption stays within 500 chars."""
    long_details = tuple(f"Detail {i}: " + "x" * 200 for i in range(3))
    story = _make_story(key_details=long_details)
    caption = compose_caption(story, _SETTINGS)
    assert len(caption) <= 500, f"Caption is {len(caption)} chars, max 500"


def test_compose_caption_long_title_within_limit():
    """Even with a very long title, caption stays within 500 chars."""
    story = _make_story(hook_title="A" * 300)
    caption = compose_caption(story, _SETTINGS)
    assert len(caption) <= 500, f"Caption is {len(caption)} chars, max 500"


def test_compose_caption_many_tags_within_limit():
    """Many tags should not push caption over 500 chars."""
    tags = tuple(f"tag{i}" for i in range(20))
    story = _make_story(tags=tags)
    caption = compose_caption(story, _SETTINGS)
    assert len(caption) <= 500, f"Caption is {len(caption)} chars, max 500"


def test_compose_caption_preserves_title():
    """The hook title should always appear in the caption."""
    story = _make_story(hook_title="Important headline here")
    caption = compose_caption(story, _SETTINGS)
    assert "Important headline here" in caption


def test_compose_caption_no_hook_or_source():
    """Caption should not contain hook line or source attribution."""
    story = _make_story(source_domain="example.com")
    caption = compose_caption(story, _SETTINGS)
    assert "Source:" not in caption
    # Caption should start with the title, not a hook phrase
    assert caption.startswith(story.hook_title)
