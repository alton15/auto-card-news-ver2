"""Tests for config module."""

from __future__ import annotations

import os

from auto_card_news_v2.config import load_settings


def test_load_settings_defaults(monkeypatch):
    monkeypatch.delenv("NEWS_RSS_FEEDS", raising=False)
    monkeypatch.delenv("NEWS_OUTPUT_DIR", raising=False)
    settings = load_settings()
    assert settings.rss_feeds == ()
    assert settings.safety_enabled is True
    assert settings.max_items == 10
    assert settings.num_cards == 6


def test_load_settings_from_env(monkeypatch):
    monkeypatch.setenv("NEWS_RSS_FEEDS", "https://a.com/rss,https://b.com/rss")
    monkeypatch.setenv("NEWS_MAX_ITEMS", "5")
    monkeypatch.setenv("NEWS_SAFETY_ENABLED", "false")
    settings = load_settings()
    assert len(settings.rss_feeds) == 2
    assert settings.max_items == 5
    assert settings.safety_enabled is False


def test_load_settings_cli_override():
    settings = load_settings(feeds_override="https://x.com/rss", output_override="/tmp/out")
    assert settings.rss_feeds == ("https://x.com/rss",)
    assert str(settings.output_dir) == "/tmp/out"
