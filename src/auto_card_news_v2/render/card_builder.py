"""Build the 5-card content structure from a Story."""

from __future__ import annotations

from email.utils import parsedate_to_datetime

from auto_card_news_v2.config import Settings
from auto_card_news_v2.models import CardContent, Story


def _format_published_date(published_at: str | None) -> str:
    """Format RSS published_at string to 'Feb 6, 2026' style."""
    if not published_at:
        return ""
    try:
        dt = parsedate_to_datetime(published_at)
        return dt.strftime("%b %-d, %Y")
    except (ValueError, TypeError):
        return ""


def build_cards(story: Story, settings: Settings) -> list[CardContent]:
    """Build a list of CardContent from a Story. Last card is CTA."""
    cards: list[CardContent] = []

    date_str = _format_published_date(story.published_at)

    # Card 1: Hook / Cover
    cards.append(CardContent(
        title=story.hook_title,
        body=story.what_happened,
        header="BREAKING",
        footer=date_str,
        card_index=1,
        card_total=5,
    ))

    # Card 2: Impact
    cards.append(CardContent(
        title="The Impact",
        body=story.impact,
        header="WHY IT MATTERS",
        card_index=2,
        card_total=5,
    ))

    # Card 3: Key Details
    bullets = "\n\n".join(f"- {d}" for d in story.key_details)
    cards.append(CardContent(
        title="Key Details",
        body=bullets,
        header="THE FACTS",
        card_index=3,
        card_total=5,
    ))

    # Card 4: What Next
    cards.append(CardContent(
        title="What's Next",
        body=story.what_next,
        header="LOOKING AHEAD",
        card_index=4,
        card_total=5,
    ))

    # Card 5: CTA
    cta_body = (
        f"{settings.brand_name}\n\n"
        f"Follow {settings.brand_handle}\n"
        "for daily news updates\n\n"
        "Save this post\n"
        "Share with friends"
    )
    cards.append(CardContent(
        title="",
        body=cta_body,
        card_index=5,
        card_total=5,
    ))

    return cards
