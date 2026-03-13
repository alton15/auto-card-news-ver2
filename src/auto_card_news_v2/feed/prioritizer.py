"""Feed item prioritization based on source domain quotas."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from auto_card_news_v2.models import FeedItem

logger = logging.getLogger(__name__)


def _is_priority(item: FeedItem, priority_domains: tuple[str, ...]) -> bool:
    """Check if a feed item belongs to a priority domain."""
    domain = item.source_domain or ""
    domain = domain.lower().removeprefix("www.")
    return any(pd.lower() in domain for pd in priority_domains)


def _count_today_by_category(
    priority_domains: tuple[str, ...],
    *,
    history_path: Path | None = None,
    tz_name: str = "Asia/Seoul",
) -> tuple[int, int]:
    """Count today's published items split by priority vs normal.

    Returns (priority_count, normal_count).
    """
    try:
        from zoneinfo import ZoneInfo
        local_tz = ZoneInfo(tz_name)
    except (ImportError, KeyError):
        from datetime import timedelta
        # Fallback for Asia/Seoul (UTC+9)
        local_tz = timezone(timedelta(hours=9))

    from auto_card_news_v2.feed.history import _history_path as default_path
    path = history_path or default_path()

    if not path.exists():
        return 0, 0

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0, 0

    urls: dict[str, str] = data.get("urls", {})
    now = datetime.now(local_tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    priority_count = 0
    normal_count = 0

    for url, timestamp_str in urls.items():
        try:
            ts = datetime.fromisoformat(timestamp_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            ts_local = ts.astimezone(local_tz)
        except (ValueError, TypeError):
            continue

        if ts_local < today_start:
            continue

        # Check if this URL belongs to a priority domain
        try:
            host = urlparse(url).hostname or ""
        except Exception:
            host = ""
        host = host.lower().removeprefix("www.")

        if any(pd.lower() in host for pd in priority_domains):
            priority_count += 1
        else:
            normal_count += 1

    return priority_count, normal_count


def prioritize_items(
    items: list[FeedItem],
    *,
    priority_domains: tuple[str, ...],
    priority_ratio: int = 8,
    daily_total: int = 12,
    history_path: Path | None = None,
    tz_name: str = "Asia/Seoul",
) -> list[FeedItem]:
    """Reorder items so the appropriate category comes first based on daily quota.

    With --limit 1, the first item will be picked. This function ensures
    the priority/normal ratio is maintained across the day.

    Args:
        items: Deduplicated, unprocessed feed items.
        priority_domains: Domains to treat as priority (e.g., soompi.com).
        priority_ratio: Target priority items per day (e.g., 8 out of 12).
        daily_total: Total expected items per day.
        history_path: Override for testing.
        tz_name: Timezone for "today" calculation.

    Returns:
        Reordered items with the appropriate category first.
    """
    if not priority_domains or not items:
        return items

    normal_ratio = daily_total - priority_ratio

    priority_items = [i for i in items if _is_priority(i, priority_domains)]
    normal_items = [i for i in items if not _is_priority(i, priority_domains)]

    if not priority_items:
        logger.info("No priority items available, using normal items")
        return normal_items
    if not normal_items:
        logger.info("No normal items available, using priority items")
        return priority_items

    p_count, n_count = _count_today_by_category(
        priority_domains, history_path=history_path, tz_name=tz_name,
    )

    logger.info(
        "Today's publish count: priority=%d/%d, normal=%d/%d",
        p_count, priority_ratio, n_count, normal_ratio,
    )

    # Determine which category should go next.
    # Calculate how "behind" each category is relative to its target.
    p_remaining = max(0, priority_ratio - p_count)
    n_remaining = max(0, normal_ratio - n_count)

    if p_remaining == 0 and n_remaining == 0:
        # Both quotas met — prefer priority
        return priority_items + normal_items

    # Pick from the category that's further behind its quota
    p_fill_rate = p_count / priority_ratio if priority_ratio > 0 else 1.0
    n_fill_rate = n_count / normal_ratio if normal_ratio > 0 else 1.0

    if p_fill_rate <= n_fill_rate:
        logger.info("Selecting priority feed (fill: %.0f%% vs %.0f%%)",
                     p_fill_rate * 100, n_fill_rate * 100)
        return priority_items + normal_items
    else:
        logger.info("Selecting normal feed (fill: %.0f%% vs %.0f%%)",
                     n_fill_rate * 100, p_fill_rate * 100)
        return normal_items + priority_items
