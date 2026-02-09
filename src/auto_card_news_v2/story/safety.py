"""PII redaction and cautious phrasing for unverified news."""

from __future__ import annotations

import re

from auto_card_news_v2.models import Story

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}")
_KR_ID_RE = re.compile(r"\d{6}[-]\d{7}")
_ADDRESS_RE = re.compile(
    r"(?:\d{1,5}\s[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct))"
    r"|(?:[\uac00-\ud7a3]+(?:시|도|군|구|읍|면|동|리)\s[\uac00-\ud7a3\d\s-]+)",
    re.IGNORECASE,
)

_CAUTION_TRIGGERS = frozenset({
    "alleged", "reportedly", "unconfirmed", "rumor", "rumour",
    "sources say", "claims",
    "의혹", "미확인", "루머", "소문", "제보", "관계자",
    "알려졌", "전해졌", "보도됐",
})

_CAUTION_PREFIX_KO = "보도에 따르면, "
_CAUTION_PREFIX_EN = "According to reports, "


def sanitize_story(story: Story, *, enabled: bool = True) -> Story:
    """Redact PII and add cautious phrasing if needed. Returns new Story."""
    if not enabled:
        return story

    what_happened = _redact(story.what_happened)
    where_when = _redact(story.where_when)
    impact = _redact(story.impact)
    what_next = _redact(story.what_next)
    key_details = tuple(_redact(d) for d in story.key_details)

    if _needs_caution(story):
        what_happened = _ensure_cautious(what_happened)

    return Story(
        hook_title=story.hook_title,
        what_happened=what_happened,
        where_when=where_when,
        impact=impact,
        key_details=key_details,
        what_next=what_next,
        tags=story.tags,
        source_domain=story.source_domain,
        source_url=story.source_url,
        published_at=story.published_at,
    )


def _redact(text: str) -> str:
    text = _EMAIL_RE.sub("", text)
    text = _KR_ID_RE.sub("", text)
    text = _PHONE_RE.sub("", text)
    text = _ADDRESS_RE.sub("", text)
    # Clean up leftover whitespace from removals
    text = re.sub(r"  +", " ", text).strip()
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text


def _needs_caution(story: Story) -> bool:
    combined = " ".join([
        story.hook_title,
        story.what_happened,
        story.impact,
        story.what_next,
    ]).lower()
    return any(trigger in combined for trigger in _CAUTION_TRIGGERS)


def _ensure_cautious(text: str) -> str:
    has_korean = any("\uac00" <= ch <= "\ud7a3" for ch in text)
    prefix = _CAUTION_PREFIX_KO if has_korean else _CAUTION_PREFIX_EN
    if text.startswith(prefix):
        return text
    return prefix + text
