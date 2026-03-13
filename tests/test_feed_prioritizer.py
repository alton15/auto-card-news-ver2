"""Tests for feed item prioritization."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from auto_card_news_v2.feed.prioritizer import (
    _is_priority,
    _count_today_by_category,
    prioritize_items,
)
from auto_card_news_v2.models import FeedItem


def _item(title: str, url: str, domain: str) -> FeedItem:
    return FeedItem(title=title, url=url, source_domain=domain)


PRIORITY_DOMAINS = ("soompi.com", "koreaboo.com")

KPOP_1 = _item("BTS news", "https://www.soompi.com/article/1", "soompi.com")
KPOP_2 = _item("BLACKPINK news", "https://www.koreaboo.com/stories/1", "koreaboo.com")
KPOP_3 = _item("NewJeans news", "https://www.soompi.com/article/2", "soompi.com")
NEWS_1 = _item("Economy update", "https://en.yna.co.kr/view/1", "en.yna.co.kr")
NEWS_2 = _item("Politics update", "https://en.yna.co.kr/view/2", "en.yna.co.kr")
NEWS_3 = _item("Sports news", "http://rss.joinsmsn.com/news/1", "rss.joinsmsn.com")


class TestIsPriority:
    def test_soompi_is_priority(self) -> None:
        assert _is_priority(KPOP_1, PRIORITY_DOMAINS) is True

    def test_koreaboo_is_priority(self) -> None:
        assert _is_priority(KPOP_2, PRIORITY_DOMAINS) is True

    def test_yna_is_not_priority(self) -> None:
        assert _is_priority(NEWS_1, PRIORITY_DOMAINS) is False

    def test_empty_priority_domains(self) -> None:
        assert _is_priority(KPOP_1, ()) is False

    def test_none_source_domain(self) -> None:
        item = FeedItem(title="test", url="https://example.com", source_domain=None)
        assert _is_priority(item, PRIORITY_DOMAINS) is False


class TestCountTodayByCategory:
    def test_empty_history(self, tmp_path: Path) -> None:
        history = tmp_path / "history.json"
        p, n = _count_today_by_category(
            PRIORITY_DOMAINS, history_path=history,
        )
        assert p == 0
        assert n == 0

    def test_counts_today_only(self, tmp_path: Path) -> None:
        history = tmp_path / "history.json"
        now = datetime.now(timezone.utc).isoformat()
        old = "2020-01-01T00:00:00+00:00"
        data = {
            "urls": {
                "https://www.soompi.com/article/1": now,
                "https://www.koreaboo.com/stories/1": now,
                "https://en.yna.co.kr/view/1": now,
                "https://www.soompi.com/article/old": old,  # yesterday
            },
        }
        history.write_text(json.dumps(data))
        p, n = _count_today_by_category(
            PRIORITY_DOMAINS, history_path=history,
        )
        assert p == 2
        assert n == 1

    def test_corrupted_history(self, tmp_path: Path) -> None:
        history = tmp_path / "history.json"
        history.write_text("not json")
        p, n = _count_today_by_category(
            PRIORITY_DOMAINS, history_path=history,
        )
        assert p == 0
        assert n == 0


class TestPrioritizeItems:
    def test_empty_items(self) -> None:
        result = prioritize_items(
            [], priority_domains=PRIORITY_DOMAINS,
        )
        assert result == []

    def test_no_priority_domains_returns_unchanged(self) -> None:
        items = [NEWS_1, KPOP_1, NEWS_2]
        result = prioritize_items(items, priority_domains=())
        assert result == items

    def test_priority_first_when_no_history(self, tmp_path: Path) -> None:
        """With no history, priority items should come first (0/8 < 0/4)."""
        items = [NEWS_1, KPOP_1, NEWS_2, KPOP_2]
        result = prioritize_items(
            items,
            priority_domains=PRIORITY_DOMAINS,
            priority_ratio=8,
            daily_total=12,
            history_path=tmp_path / "history.json",
        )
        # Priority items should be first
        assert result[0].source_domain in ("soompi.com", "koreaboo.com")
        assert result[1].source_domain in ("soompi.com", "koreaboo.com")

    def test_normal_first_when_priority_ahead(self, tmp_path: Path) -> None:
        """When priority quota is more filled, normal items should come first."""
        history = tmp_path / "history.json"
        now = datetime.now(timezone.utc).isoformat()
        # 7 priority published, 0 normal → priority fill 87%, normal fill 0%
        urls = {}
        for i in range(7):
            urls[f"https://www.soompi.com/article/{i}"] = now
        history.write_text(json.dumps({"urls": urls}))

        items = [KPOP_3, NEWS_1, NEWS_2]
        result = prioritize_items(
            items,
            priority_domains=PRIORITY_DOMAINS,
            priority_ratio=8,
            daily_total=12,
            history_path=history,
        )
        # Normal should come first since priority is way ahead
        assert result[0].source_domain == "en.yna.co.kr"

    def test_priority_first_when_normal_ahead(self, tmp_path: Path) -> None:
        """When normal quota is more filled, priority items should come first."""
        history = tmp_path / "history.json"
        now = datetime.now(timezone.utc).isoformat()
        # 0 priority, 3 normal → normal fill 75%, priority fill 0%
        urls = {
            f"https://en.yna.co.kr/view/{i}": now for i in range(3)
        }
        history.write_text(json.dumps({"urls": urls}))

        items = [NEWS_3, KPOP_1, KPOP_2]
        result = prioritize_items(
            items,
            priority_domains=PRIORITY_DOMAINS,
            priority_ratio=8,
            daily_total=12,
            history_path=history,
        )
        assert result[0].source_domain in ("soompi.com", "koreaboo.com")

    def test_only_priority_items_available(self, tmp_path: Path) -> None:
        items = [KPOP_1, KPOP_2]
        result = prioritize_items(
            items,
            priority_domains=PRIORITY_DOMAINS,
            history_path=tmp_path / "history.json",
        )
        assert len(result) == 2
        assert all(_is_priority(i, PRIORITY_DOMAINS) for i in result)

    def test_only_normal_items_available(self, tmp_path: Path) -> None:
        items = [NEWS_1, NEWS_2]
        result = prioritize_items(
            items,
            priority_domains=PRIORITY_DOMAINS,
            history_path=tmp_path / "history.json",
        )
        assert len(result) == 2
        assert all(not _is_priority(i, PRIORITY_DOMAINS) for i in result)
