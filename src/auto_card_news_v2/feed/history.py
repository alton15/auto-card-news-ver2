"""Persistent publish history to prevent cross-run duplicate publishing."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from auto_card_news_v2.models import FeedItem

logger = logging.getLogger(__name__)

_HISTORY_DIR = Path.home() / ".card-news"
_HISTORY_FILE = _HISTORY_DIR / "publish_history.json"


def _history_path() -> Path:
    """Return the history file path (test-friendly seam)."""
    return _HISTORY_FILE


def load_history(*, history_path: Path | None = None) -> set[str]:
    """Load published URL set from disk."""
    path = history_path or _history_path()
    if not path.exists():
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Corrupted history file, starting fresh")
        return set()

    urls = data.get("urls", {})
    return set(urls.keys())


def save_url(url: str, *, history_path: Path | None = None) -> None:
    """Append a single published URL to the history file."""
    path = history_path or _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    urls: dict[str, str] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            urls = data.get("urls", {})
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupted history file, overwriting")

    normalized = url.rstrip("/").lower()
    urls[normalized] = datetime.now(timezone.utc).isoformat()

    path.write_text(
        json.dumps({"urls": urls}, indent=2),
        encoding="utf-8",
    )
    logger.info("Saved URL to publish history: %s", normalized)


def filter_already_published(
    items: list[FeedItem],
    *,
    history_path: Path | None = None,
) -> list[FeedItem]:
    """Remove items whose URLs already appear in the publish history."""
    published = load_history(history_path=history_path)
    if not published:
        return items

    result: list[FeedItem] = []
    for item in items:
        normalized = item.url.rstrip("/").lower()
        if normalized in published:
            logger.info("Skipping already-published: %s", item.url)
        else:
            result.append(item)
    return result
