"""Hashtag generation strategy for Threads posts."""

from __future__ import annotations

import re

_CATEGORY_TAGS: dict[str, list[str]] = {
    "breaking": ["#BreakingNews", "#Breaking"],
    "politics": ["#Politics", "#Government"],
    "business": ["#Business", "#Economy"],
    "technology": ["#Tech", "#Technology"],
    "science": ["#Science", "#Research"],
    "health": ["#Health", "#Wellness"],
    "sports": ["#Sports", "#Athletics"],
    "entertainment": ["#Entertainment", "#Culture"],
    "world": ["#WorldNews", "#International"],
}

_CATEGORY_KEYWORDS: dict[str, frozenset[str]] = {
    "politics": frozenset({"election", "government", "president", "congress", "vote",
                           "정치", "대통령", "국회", "선거", "정부"}),
    "business": frozenset({"market", "stock", "economy", "company", "investment",
                           "경제", "시장", "기업", "투자", "주식"}),
    "technology": frozenset({"ai", "tech", "software", "app", "digital",
                             "기술", "인공지능", "소프트웨어", "디지털"}),
    "science": frozenset({"research", "study", "scientist", "discovery",
                          "연구", "과학", "발견"}),
    "health": frozenset({"health", "medical", "hospital", "vaccine", "disease",
                         "건강", "의료", "병원", "백신"}),
    "sports": frozenset({"game", "match", "player", "team", "championship",
                         "경기", "선수", "팀", "우승"}),
}

_MAX_HASHTAGS = 8
_MIN_HASHTAGS = 5


def build_hashtags(tags: tuple[str, ...], title: str = "") -> list[str]:
    """Build an optimized hashtag list for Threads."""
    result: list[str] = ["#CardNews", "#DailyNews"]

    category = _detect_category(tags, title)
    if category and category in _CATEGORY_TAGS:
        result.extend(_CATEGORY_TAGS[category][:1])

    for tag in tags:
        cleaned = re.sub(r"[^a-zA-Z0-9\uac00-\ud7a3]", "", tag)
        if cleaned and len(cleaned) >= 2:
            hashtag = f"#{cleaned}"
            if hashtag not in result:
                result.append(hashtag)
        if len(result) >= _MAX_HASHTAGS:
            break

    while len(result) < _MIN_HASHTAGS and tags:
        result.append("#News")
        break

    return result[:_MAX_HASHTAGS]


def _detect_category(tags: tuple[str, ...], title: str) -> str | None:
    combined = " ".join(tags).lower() + " " + title.lower()
    best_category = None
    best_score = 0

    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category
