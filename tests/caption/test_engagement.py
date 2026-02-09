"""Tests for engagement hooks, CTAs, and questions."""

from __future__ import annotations

from auto_card_news_v2.caption.engagement import pick_cta, pick_hook, pick_question


def test_pick_hook_returns_string():
    result = pick_hook("some news title")
    assert isinstance(result, str)
    assert len(result) > 0


def test_pick_hook_deterministic():
    a = pick_hook("same seed")
    b = pick_hook("same seed")
    assert a == b


def test_pick_hook_varies_by_seed():
    results = {pick_hook(f"seed-{i}") for i in range(20)}
    assert len(results) > 1


def test_pick_cta_returns_string():
    assert len(pick_cta("test")) > 0


def test_pick_question_returns_string():
    assert len(pick_question("test")) > 0
