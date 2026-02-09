"""Engagement hooks, CTAs, and questions for Threads captions."""

from __future__ import annotations

import hashlib

_HOOK_TEMPLATES = (
    "Here is what you need to know:",
    "This just happened:",
    "Important update:",
    "Did you see this?",
    "You should know about this:",
    "This changes everything:",
    "Breaking it down for you:",
    "The story everyone is talking about:",
)

_CTA_TEMPLATES = (
    "Follow for daily news updates",
    "Save this for later",
    "Share with someone who needs to know",
    "Turn on notifications so you never miss out",
    "Follow for more news breakdowns",
    "Double tap if you found this useful",
)

_QUESTION_TEMPLATES = (
    "What do you think about this?",
    "Were you expecting this?",
    "How does this affect you?",
    "Share your thoughts below",
    "Did you already know about this?",
    "What should happen next?",
)


def pick_hook(seed: str) -> str:
    """Pick a hook line deterministically based on content seed."""
    return _pick(seed, _HOOK_TEMPLATES, "hook")


def pick_cta(seed: str) -> str:
    """Pick a CTA line deterministically based on content seed."""
    return _pick(seed, _CTA_TEMPLATES, "cta")


def pick_question(seed: str) -> str:
    """Pick an engagement question deterministically based on content seed."""
    return _pick(seed, _QUESTION_TEMPLATES, "question")


def _pick(seed: str, templates: tuple[str, ...], salt: str) -> str:
    """Deterministic selection using hash of seed + salt."""
    digest = hashlib.md5(f"{salt}:{seed}".encode(), usedforsecurity=False).hexdigest()
    index = int(digest[:8], 16) % len(templates)
    return templates[index]
