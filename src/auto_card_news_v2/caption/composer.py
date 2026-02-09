"""Assemble full Threads caption from story and engagement elements."""

from __future__ import annotations

from auto_card_news_v2.caption.engagement import pick_cta, pick_hook, pick_question
from auto_card_news_v2.caption.hashtags import build_hashtags
from auto_card_news_v2.config import Settings
from auto_card_news_v2.models import Story

_THREADS_MAX_CHARS = 500


def compose_caption(story: Story, settings: Settings) -> str:
    """Build a complete Threads caption within the 500-char limit.

    Priority order when trimming to fit:
        1. Remove hashtags
        2. Remove engagement question
        3. Remove CTA
        4. Truncate bullet details
    """
    seed = story.hook_title

    cta = pick_cta(seed)
    question = pick_question(seed)
    hashtags = " ".join(build_hashtags(story.tags, story.hook_title))
    bullets = story.key_details[:3]

    caption = _assemble(story.hook_title, bullets, cta, question, hashtags)
    if len(caption) <= _THREADS_MAX_CHARS:
        return caption

    # 1. Drop hashtags
    caption = _assemble(story.hook_title, bullets, cta, question, "")
    if len(caption) <= _THREADS_MAX_CHARS:
        return caption

    # 2. Drop engagement question
    caption = _assemble(story.hook_title, bullets, cta, "", "")
    if len(caption) <= _THREADS_MAX_CHARS:
        return caption

    # 3. Drop CTA
    caption = _assemble(story.hook_title, bullets, "", "", "")
    if len(caption) <= _THREADS_MAX_CHARS:
        return caption

    # 4. Reduce bullets one at a time
    for n in range(len(bullets) - 1, -1, -1):
        caption = _assemble(story.hook_title, bullets[:n], "", "", "")
        if len(caption) <= _THREADS_MAX_CHARS:
            return caption

    # 5. Last resort: hard truncate
    caption = _assemble(story.hook_title, (), "", "", "")
    if len(caption) > _THREADS_MAX_CHARS:
        caption = caption[:_THREADS_MAX_CHARS]

    return caption


def _assemble(
    title: str,
    bullets: tuple[str, ...] | list[str],
    cta: str,
    question: str,
    hashtags: str,
) -> str:
    """Join caption parts into a single string, skipping empty sections."""
    parts: list[str] = []

    parts.append(title)

    if bullets:
        parts.append("")
        for detail in bullets:
            parts.append(f"  {detail}")

    if cta:
        parts.append("")
        parts.append(cta)

    if question:
        parts.append("")
        parts.append(question)

    if hashtags:
        parts.append("")
        parts.append(hashtags)

    return "\n".join(parts)
