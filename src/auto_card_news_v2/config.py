"""Settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application settings. All values come from NEWS_* env vars."""

    rss_feeds: tuple[str, ...]
    output_dir: Path
    safety_enabled: bool
    max_items: int
    num_cards: int
    brand_name: str
    brand_handle: str
    dry_run: bool = False
    threads_user_id: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""


def load_settings(
    *,
    feeds_override: str | None = None,
    output_override: str | None = None,
    dry_run: bool = False,
) -> Settings:
    """Build Settings from environment variables with optional CLI overrides."""
    raw_feeds = feeds_override or os.getenv("NEWS_RSS_FEEDS", "")
    feeds = tuple(u.strip() for u in raw_feeds.split(",") if u.strip())

    output_dir = Path(output_override or os.getenv("NEWS_OUTPUT_DIR", "./output"))

    safety_str = os.getenv("NEWS_SAFETY_ENABLED", "true").lower()
    safety_enabled = safety_str not in ("false", "0", "no")

    max_items = int(os.getenv("NEWS_MAX_ITEMS", "10"))
    num_cards = int(os.getenv("NEWS_NUM_CARDS", "6"))
    brand_name = os.getenv("NEWS_BRAND_NAME", "Card News")
    brand_handle = os.getenv("NEWS_BRAND_HANDLE", "@cardnews")

    threads_user_id = os.getenv("THREADS_USER_ID", "")
    cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET", "")

    return Settings(
        rss_feeds=feeds,
        output_dir=output_dir,
        safety_enabled=safety_enabled,
        max_items=max_items,
        num_cards=num_cards,
        brand_name=brand_name,
        brand_handle=brand_handle,
        dry_run=dry_run,
        threads_user_id=threads_user_id,
        cloudinary_cloud_name=cloudinary_cloud_name,
        cloudinary_api_key=cloudinary_api_key,
        cloudinary_api_secret=cloudinary_api_secret,
    )
