"""Tests for safety / PII redaction."""

from __future__ import annotations

from auto_card_news_v2.models import Story
from auto_card_news_v2.story.safety import sanitize_story


def _make_story(**overrides) -> Story:
    defaults = dict(
        hook_title="Test",
        what_happened="Contact user@example.com for details.",
        where_when="Seoul",
        impact="No impact",
        key_details=("Detail 1",),
        what_next="Nothing",
        tags=("test",),
    )
    defaults.update(overrides)
    return Story(**defaults)


def test_redact_email():
    story = _make_story(what_happened="Email me at john@example.com please.")
    result = sanitize_story(story)
    assert "john@example.com" not in result.what_happened


def test_redact_phone():
    story = _make_story(what_happened="Call 010-1234-5678 now.")
    result = sanitize_story(story)
    assert "010-1234-5678" not in result.what_happened


def test_caution_phrase_added():
    story = _make_story(what_happened="The alleged criminal was seen nearby.")
    result = sanitize_story(story)
    assert result.what_happened.startswith("According to reports, ")


def test_safety_disabled():
    story = _make_story(what_happened="Email me at john@example.com please.")
    result = sanitize_story(story, enabled=False)
    assert "john@example.com" in result.what_happened
