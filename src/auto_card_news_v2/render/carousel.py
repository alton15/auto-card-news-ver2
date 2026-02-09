"""Multi-card carousel rendering via HTML/CSS + Playwright screenshot."""

from __future__ import annotations

import html
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import Browser, sync_playwright

from auto_card_news_v2.config import Settings
from auto_card_news_v2.models import CardContent, Story
from auto_card_news_v2.render.card_builder import build_cards
from auto_card_news_v2.render.theme import Theme

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_carousel(
    story: Story,
    output_dir: Path,
    settings: Settings,
    *,
    theme: Theme | None = None,
) -> list[Path]:
    """Render all cards for a story and save as PNGs. Returns image paths."""
    if theme is None:
        theme = Theme.modern_bold()

    cards = build_cards(story, settings)
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,
    )
    template = env.get_template("card.html")
    css_vars = theme.css_vars()

    paths: list[Path] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": theme.width, "height": theme.height})

        for card in cards:
            path = output_dir / f"card_{card.card_index:02d}.png"
            html_content = _build_html(template, card, css_vars, settings)
            page.set_content(html_content, wait_until="networkidle")
            page.screenshot(path=str(path), type="png")
            paths.append(path)

        browser.close()

    return paths


def render_carousel_with_browser(
    story: Story,
    output_dir: Path,
    settings: Settings,
    browser: Browser,
    *,
    theme: Theme | None = None,
) -> list[Path]:
    """Render cards reusing an existing Playwright browser instance."""
    if theme is None:
        theme = Theme.modern_bold()

    cards = build_cards(story, settings)
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,
    )
    template = env.get_template("card.html")
    css_vars = theme.css_vars()

    paths: list[Path] = []
    page = browser.new_page(viewport={"width": theme.width, "height": theme.height})

    for card in cards:
        path = output_dir / f"card_{card.card_index:02d}.png"
        html_content = _build_html(template, card, css_vars, settings)
        page.set_content(html_content, wait_until="networkidle")
        page.screenshot(path=str(path), type="png")
        paths.append(path)

    page.close()
    return paths


def _build_html(
    template,
    card: CardContent,
    css_vars: dict[str, str],
    settings: Settings,
) -> str:
    """Build the HTML string for a single card."""
    position = f"{card.card_index} / {card.card_total}"
    card_type = _detect_card_type(card)

    context = {
        **css_vars,
        "body": _format_body(card.body),
        "title": html.escape(html.unescape(card.title)) if card.title else "",
        "header": html.escape(card.header) if card.header else "",
        "footer": html.escape(card.footer) if card.footer else "",
        "position": position,
        "card_type": card_type,
        "card_number": card.card_index,
        "brand_name": html.escape(settings.brand_name),
        "brand_handle": html.escape(settings.brand_handle),
        "bullet_items": [],
    }

    if card_type == "bullets":
        items = [
            line.lstrip("- ").strip()
            for line in card.body.split("\n")
            if line.strip() and line.strip().startswith("-")
        ]
        context["bullet_items"] = [html.escape(html.unescape(item)) for item in items]

    return template.render(**context)


def _detect_card_type(card: CardContent) -> str:
    """Detect the card type for template rendering."""
    if card.card_index == 1:
        return "cover"
    if card.card_index == card.card_total:
        return "cta"
    if card.body.strip().startswith("-"):
        return "bullets"
    return "body"


def _format_body(text: str) -> str:
    """Normalize HTML entities, escape, and convert newlines to <br>."""
    clean = html.unescape(text)
    escaped = html.escape(clean)
    return escaped.replace("\n", "<br>")
