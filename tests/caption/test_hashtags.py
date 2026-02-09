"""Tests for hashtag generation."""

from __future__ import annotations

from auto_card_news_v2.caption.hashtags import build_hashtags


def test_build_hashtags_includes_base_tags():
    tags = ("subway", "transit")
    result = build_hashtags(tags)
    assert "#CardNews" in result
    assert "#DailyNews" in result


def test_build_hashtags_max_count():
    tags = ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j")
    result = build_hashtags(tags)
    assert len(result) <= 8


def test_build_hashtags_no_duplicates():
    tags = ("news", "news", "update")
    result = build_hashtags(tags)
    assert len(result) == len(set(result))


def test_build_hashtags_detects_category():
    tags = ("election", "president", "vote")
    result = build_hashtags(tags, title="Election results")
    assert any("Politic" in h for h in result)
