"""Shared test fixtures."""

from __future__ import annotations

import pytest

from auto_card_news_v2.models import FeedItem, Story


@pytest.fixture
def sample_feed_item() -> FeedItem:
    return FeedItem(
        title="City subway service briefly suspended after signal issue",
        url="https://example.com/news/subway-suspension",
        summary="The subway was shut down for 45 minutes due to a signaling fault. No injuries were reported. A hardware review has been scheduled.",
        published_at="2026-01-30T08:00:00Z",
        source_domain="example.com",
    )


@pytest.fixture
def sample_story() -> Story:
    return Story(
        hook_title="City subway suspended after signal issue",
        what_happened="The subway was shut down for 45 minutes due to a signaling fault.",
        where_when="2026-01-30T08:00:00Z | example.com",
        impact="No injuries were reported. Thousands of commuters were delayed.",
        key_details=(
            "Service suspended for 45 minutes",
            "Signal fault identified as root cause",
            "No injuries reported",
            "Hardware review scheduled",
        ),
        what_next="A hardware review has been scheduled.",
        tags=("subway", "transit", "safety", "signal"),
        source_domain="example.com",
        source_url="https://example.com/news/subway-suspension",
        published_at="2026-01-30T08:00:00Z",
    )
