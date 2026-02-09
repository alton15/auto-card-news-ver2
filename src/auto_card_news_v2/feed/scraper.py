"""Scrape full article body text from news URLs using Playwright."""

from __future__ import annotations

from playwright.sync_api import Browser, Page

# Selectors ordered by specificity - try most specific first
_ARTICLE_SELECTORS = [
    ".story-news",        # Yonhap English
    ".article-txt",       # Korea Herald
    "#article_body",      # JoongAng Daily
    "#viewContent",       # Hanmi Ilbo
    "article .body",
    ".article-body",
    ".article_body",
    "#articleBody",
    ".content-body",
    "article p",
    ".story-body",
    "article",
]

_MIN_BODY_LENGTH = 150


def scrape_article(url: str, *, browser: Browser) -> str | None:
    """Fetch full article text from a URL. Returns None on failure."""
    page: Page | None = None
    try:
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=15000)

        for selector in _ARTICLE_SELECTORS:
            elements = page.query_selector_all(selector)
            if not elements:
                continue
            text = " ".join(el.inner_text() for el in elements).strip()
            if len(text) >= _MIN_BODY_LENGTH:
                return _clean_article_text(text)

        return None
    except Exception:
        return None
    finally:
        if page:
            page.close()


def _clean_article_text(text: str) -> str:
    """Remove common noise from scraped article text."""
    lines = text.split("\n")
    cleaned: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip common noise patterns
        lower = line.lower()
        if any(noise in lower for noise in (
            "copyright", "all rights reserved", "©",
            "subscribe", "sign up", "newsletter",
            "advertisement", "promoted content",
            "share this", "related articles",
            "photo not for sale", "not for sale",
            "getty images", "(yonhap)", "(reuters)",
            "click here", "read more", "send us",
        )):
            continue
        # Skip bylines like "By Kim Eun-jung"
        if line.startswith("By ") and len(line) < 40:
            continue
        # Skip very short lines (likely captions/bylines)
        if len(line) < 15 and not line.endswith("."):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)
