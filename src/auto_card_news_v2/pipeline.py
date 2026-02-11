"""End-to-end pipeline: fetch -> scrape -> summarize -> render -> caption -> package."""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import replace
from pathlib import Path

from playwright.sync_api import sync_playwright

from auto_card_news_v2.caption import compose_caption
from auto_card_news_v2.config import Settings
from auto_card_news_v2.feed import deduplicate, fetch_feed, filter_already_published, parse_feed
from auto_card_news_v2.feed.history import save_url
from auto_card_news_v2.feed.scraper import scrape_article
from auto_card_news_v2.models import FeedItem, ThreadsPost
from auto_card_news_v2.output import package_output
from auto_card_news_v2.render.carousel import render_carousel_with_browser
from auto_card_news_v2.story import build_story, sanitize_story

logger = logging.getLogger(__name__)

_MAX_OUTPUT_DIRS = 5


def run_pipeline(settings: Settings) -> list[ThreadsPost]:
    """Run the full card news generation pipeline."""
    items = _fetch_all_feeds(settings)
    items = deduplicate(items)
    items = filter_already_published(items)
    items = items[: settings.max_items]

    if settings.dry_run:
        _print_dry_run(items)
        return []

    posts: list[ThreadsPost] = []

    with sync_playwright() as pw:
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
        browser = pw.chromium.launch(executable_path=executable) if executable else pw.chromium.launch()

        for item in items:
            try:
                # Scrape full article body
                full_text = scrape_article(item.url, browser=browser)
                if full_text:
                    item = replace(item, full_text=full_text)

                post = _process_item(item, settings, browser)
                posts.append(post)
                save_url(item.url)
            except Exception as exc:
                print(f"Warning: Failed to process '{item.title}': {exc}")

        browser.close()

    _cleanup_old_outputs(settings.output_dir)
    return posts


def _fetch_all_feeds(settings: Settings) -> list[FeedItem]:
    """Fetch and parse all configured RSS feeds."""
    all_items: list[FeedItem] = []
    for url in settings.rss_feeds:
        try:
            data = fetch_feed(url)
            items = parse_feed(data, feed_url=url)
            all_items.extend(items)
        except Exception as exc:
            print(f"Warning: Failed to fetch '{url}': {exc}")
    return all_items


def _process_item(item: FeedItem, settings: Settings, browser) -> ThreadsPost:
    """Process a single feed item through the full pipeline."""
    story = build_story(item)
    story = sanitize_story(story, enabled=settings.safety_enabled)

    temp_dir = settings.output_dir / "_temp_render"
    image_paths = render_carousel_with_browser(
        story, temp_dir, settings, browser,
    )
    caption = compose_caption(story, settings)
    post = package_output(story, image_paths, caption, settings.output_dir)

    # Clean up temp render directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

    return post


def _cleanup_old_outputs(output_dir: Path) -> None:
    """Remove oldest output directories when count exceeds _MAX_OUTPUT_DIRS."""
    if not output_dir.exists():
        return

    dirs = sorted(
        (d for d in output_dir.iterdir() if d.is_dir() and not d.name.startswith("_")),
        key=lambda d: d.name,
    )

    to_remove = dirs[:-_MAX_OUTPUT_DIRS] if len(dirs) > _MAX_OUTPUT_DIRS else []
    for d in to_remove:
        shutil.rmtree(d, ignore_errors=True)
        logger.info("Cleaned up old output: %s", d.name)


def _print_dry_run(items: list[FeedItem]) -> None:
    print(f"Dry run: {len(items)} items would be processed:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item.title}")
        print(f"     URL: {item.url}")
        print(f"     Source: {item.source_domain}")
