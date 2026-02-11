"""Tests for carousel rendering."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from auto_card_news_v2.config import Settings, load_settings
from auto_card_news_v2.models import CardContent
from auto_card_news_v2.render.carousel import _build_html, render_carousel
from auto_card_news_v2.render.theme import Theme


def test_render_carousel_creates_pngs(sample_story, tmp_path):
    settings = load_settings(feeds_override="https://example.com/rss")
    paths = render_carousel(sample_story, tmp_path, settings)
    assert len(paths) == 5
    for p in paths:
        assert p.exists()
        assert p.suffix == ".png"
        assert p.stat().st_size > 0


def _load_template():
    template_dir = Path(__file__).resolve().parent.parent.parent / "src" / "auto_card_news_v2" / "render" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=False)
    return env.get_template("card.html")


def _make_settings() -> Settings:
    return Settings(
        rss_feeds=("https://example.com/rss",),
        output_dir="./output",
        safety_enabled=True,
        max_items=10,
        num_cards=5,
        brand_name="Card News",
        brand_handle="@cardnews",
    )


def _extract_body(html_str: str) -> str:
    """Extract just the <body> content, excluding <style> CSS."""
    start = html_str.index("<body>")
    end = html_str.index("</body>") + len("</body>")
    return html_str[start:end]


def test_build_html_cover():
    template = _load_template()
    card = CardContent(title="Test", body="Body text", card_index=1, card_total=5, header="NEWS")
    theme = Theme.modern_bold()
    html = _build_html(template, card, theme.css_vars(), _make_settings())
    body = _extract_body(html)
    assert "accent-bar" in body
    assert "cover-deco" in body
