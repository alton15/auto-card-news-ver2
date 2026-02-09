"""Tests for carousel rendering."""

from __future__ import annotations

from pathlib import Path

from auto_card_news_v2.config import load_settings
from auto_card_news_v2.render.carousel import render_carousel


def test_render_carousel_creates_pngs(sample_story, tmp_path):
    settings = load_settings(feeds_override="https://example.com/rss")
    paths = render_carousel(sample_story, tmp_path, settings)
    assert len(paths) == 5
    for p in paths:
        assert p.exists()
        assert p.suffix == ".png"
        assert p.stat().st_size > 0
