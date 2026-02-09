"""Deterministic heuristic summarization of feed items into stories."""

from __future__ import annotations

import html
import re
from collections import Counter

from auto_card_news_v2.models import FeedItem, Story

_STOPWORDS_EN = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "be", "been", "has",
    "have", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "not", "no", "it", "its", "this",
    "that", "from", "as", "if", "so", "up", "about", "into", "over",
    "after", "s", "t", "he", "she", "they", "we", "you", "i",
})

_STOPWORDS_KO = frozenset({
    "의", "가", "이", "은", "는", "을", "를", "에", "에서", "와", "과",
    "도", "로", "으로", "에게", "한", "하는", "및", "등", "더", "또",
    "그", "이런", "저", "것", "수", "때", "중",
})

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|(?<=다\.)\s*|(?<=요\.)\s*")

# Common abbreviations that should not be treated as sentence boundaries
_ABBREVIATION_RE = re.compile(
    r"\b(?:S|U|R|N|E|W|Dr|Mr|Mrs|Ms|Prof|Gen|Gov|Rep|Sen|Jr|Sr|Inc|Corp|Ltd|Co|vs|etc|approx"
    r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
    r"|No|Vol|Dept|Ave|St|Blvd|Ft)\.\s",
    re.IGNORECASE,
)

# RSS wire-service prefixes to strip: (LEAD), (1st LD), (URGENT), (ATTN:...),
# (PHOTO:...), (END), (RECAP), (CORRECTED) etc.
_WIRE_PREFIX_RE = re.compile(
    r"^\s*\("
    r"(?:LEAD|URGENT|ATTN[^)]*|PHOTO[^)]*|END|RECAP|CORRECTED|"
    r"(?:1st|2nd|3rd|[0-9]+th)\s+LD[^)]*)"
    r"\)\s*",
    re.IGNORECASE,
)

# Noise patterns to filter out from scraped text
_NOISE_PATTERNS = re.compile(
    r"(?i)"
    r"(photo not for sale|yonhap\)|all rights reserved|"
    r"copyright\b|©|getty images|afp|reuters\)|ap\)|"
    r"^\s*by\s+[a-z][\w\s-]{2,30}$|"  # bylines like "By Kim Eun-jung"
    r"^\s*\([^)]*\)\s*$|"  # standalone parenthetical like "(Yonhap)"
    r"^\s*\w+@\w+\.\w+|"  # email addresses
    r"send us your|click here|read more|subscribe|"
    r"related article|recommended|advertisement)",
    re.MULTILINE,
)
_IMPACT_KEYWORDS = frozenset({
    "impact", "effect", "affect", "result", "consequence", "cause",
    "lead", "significant", "major", "critical", "concern", "risk",
    "billion", "million", "percent", "growth", "decline", "drop",
    "영향", "결과", "파급", "피해", "변화", "충격", "위기",
})
_FUTURE_KEYWORDS = frozenset({
    "expect", "plan", "will", "future", "next", "upcoming", "forecast",
    "outlook", "prospect", "remain", "continue", "going forward",
    "예정", "전망", "계획", "향후", "예상", "앞으로",
})


def build_story(item: FeedItem) -> Story:
    """Transform a FeedItem into a structured Story using heuristics."""
    text = _combined_text(item)
    sentences = _split_sentences(text)

    hook_title = _shorten(_decode_html(_strip_wire_prefixes(item.title)), max_len=120)
    what_happened = _build_what_happened(sentences, item.title)
    where_when = _extract_where_when(sentences, item)
    impact = _build_impact(sentences)
    what_next = _build_what_next(sentences)
    key_details = _build_key_details(sentences)
    tags = _extract_tags(text)

    return Story(
        hook_title=hook_title,
        what_happened=what_happened,
        where_when=where_when,
        impact=impact,
        key_details=tuple(key_details),
        what_next=what_next,
        tags=tuple(tags),
        source_domain=item.source_domain,
        source_url=item.url,
        published_at=item.published_at,
    )


def _strip_wire_prefixes(text: str) -> str:
    """Remove wire-service prefixes like (LEAD), (URGENT), (ATTN:...) etc."""
    return _WIRE_PREFIX_RE.sub("", text).strip()


def _normalize_whitespace(text: str) -> str:
    """Collapse newlines and multiple spaces into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def _decode_html(text: str) -> str:
    """Decode HTML entities and remove leftover tags/nbsp."""
    decoded = html.unescape(text)
    # Remove leftover HTML tags
    decoded = re.sub(r"<[^>]+>", " ", decoded)
    # Clean up non-breaking spaces and multiple spaces
    decoded = decoded.replace("\xa0", " ")
    return re.sub(r"\s+", " ", decoded).strip()


def _ensure_period(text: str) -> str:
    """Ensure text ends with a period for proper sentence splitting."""
    text = text.rstrip()
    if text and text[-1] not in ".!?":
        return text + "."
    return text


def _combined_text(item: FeedItem) -> str:
    title = _decode_html(_strip_wire_prefixes(item.title))
    if item.full_text:
        cleaned = _decode_html(_strip_wire_prefixes(item.full_text))
        # Remove duplicated title from full_text start
        clean_normalized = _normalize_whitespace(cleaned)
        title_lower = title.lower()
        if clean_normalized.lower().startswith(title_lower):
            cleaned = clean_normalized[len(title):].lstrip()
        # Add period after title to ensure proper sentence boundary
        return _normalize_whitespace(f"{_ensure_period(title)} {cleaned}")
    parts = [_ensure_period(title)]
    if item.summary:
        parts.append(_decode_html(_strip_wire_prefixes(item.summary)))
    return _normalize_whitespace(" ".join(parts))


def _split_sentences(text: str) -> list[str]:
    # Protect abbreviations by replacing ". " with a placeholder
    _PLACEHOLDER = "\u2060.\u2060"
    protected = _ABBREVIATION_RE.sub(
        lambda m: m.group().replace(". ", f"{_PLACEHOLDER} "),
        text,
    )
    # Protect "U.S." as a common pattern
    protected = re.sub(r"\bU\.S\.", "U\u2060.S\u2060.", protected)
    # Protect numbers followed by period + space (e.g., "1. ", "30. ")
    protected = re.sub(r"(\d)\.\s", lambda m: m.group(1) + "\u2060. ", protected)

    raw = _SENTENCE_SPLIT_RE.split(protected)
    # Restore abbreviation periods
    sentences = [s.replace("\u2060", "").strip() for s in raw if s.strip()]
    sentences = [s for s in sentences if len(s) > 15]
    return [s for s in sentences if not _is_noise(s)]


def _is_noise(sentence: str) -> bool:
    """Check if a sentence is noise (bylines, photo credits, etc.)."""
    return bool(_NOISE_PATTERNS.search(sentence))


def _shorten(text: str, *, max_len: int) -> str:
    """Shorten text to max_len, cutting at sentence boundaries.

    Prefers dropping entire sentences over truncating mid-sentence.
    Falls back to period-boundary or word-boundary only when no
    complete sentence fits within the limit.
    """
    if len(text) <= max_len:
        return text

    # Use abbreviation-aware splitting to avoid cutting at "S." etc.
    sentences = _split_sentences(text)
    result = ""
    for sentence in sentences:
        candidate = f"{result} {sentence}".strip() if result else sentence
        if len(candidate) <= max_len:
            result = candidate
        else:
            break

    if result and len(result) > 15:
        return result

    # Fallback: no complete sentence fits; cut at word boundary
    truncated = text[:max_len].rsplit(" ", 1)[0]
    # Find the last period that isn't part of an abbreviation
    last_good_period = -1
    for m in re.finditer(r"\.\s", truncated):
        pos = m.start()
        # Extract the word before the period
        before_text = truncated[:pos]
        word_match = re.search(r"(\w+)$", before_text)
        if word_match:
            word = word_match.group(1)
            # Check if this word is a known abbreviation
            if _ABBREVIATION_RE.match(f"{word}. "):
                continue
        last_good_period = pos

    if last_good_period > max_len // 3:
        return truncated[: last_good_period + 1]
    # Cut at last word boundary, ensuring clean ending
    clean = truncated.rstrip(",;:\" '")
    return clean.rstrip()


def _build_what_happened(sentences: list[str], title: str) -> str:
    """Build concise 'what happened' from first relevant sentences."""
    if not sentences:
        return title

    title_words = set(title.lower().split())
    supporting: list[str] = []
    for s in sentences[:6]:
        s_words = set(s.lower().split())
        overlap = len(title_words & s_words) / max(len(title_words), 1)
        if overlap < 0.7 and len(s) > 20:
            supporting.append(_shorten(s, max_len=300))
        if len(supporting) >= 2:
            break

    if supporting:
        result = " ".join(supporting[:2])
    else:
        result = " ".join(sentences[:2])
    return _shorten(result, max_len=500)


def _build_impact(sentences: list[str]) -> str:
    """Extract impact/significance sentences."""
    matches = _find_by_keywords(sentences, _IMPACT_KEYWORDS, max_results=2)
    if matches:
        result = " ".join(_shorten(m, max_len=300) for m in matches)
    elif len(sentences) > 2:
        mid = len(sentences) // 2
        result = sentences[mid]
    else:
        result = sentences[-1] if sentences else ""
    return _shorten(result, max_len=500)


def _build_what_next(sentences: list[str]) -> str:
    """Extract forward-looking content, preferring latter half of the article."""
    if not sentences:
        return ""
    # Search from the latter half of sentences first for forward-looking content
    mid = max(len(sentences) // 2, 1)
    latter_half = sentences[mid:]
    matches = _find_by_keywords(latter_half, _FUTURE_KEYWORDS, max_results=2)
    if not matches:
        # Fall back to searching all sentences
        matches = _find_by_keywords(sentences, _FUTURE_KEYWORDS, max_results=2)
    if matches:
        result = " ".join(_shorten(m, max_len=300) for m in matches)
    else:
        result = sentences[-1]
    return _shorten(result, max_len=500)


def _build_key_details(sentences: list[str], *, max_items: int = 4) -> list[str]:
    """Extract distinct key details, preferring data-rich sentences."""
    if len(sentences) <= 2:
        return [_clean_detail(s) for s in sentences]

    scored: list[tuple[float, int, str]] = []
    for idx, s in enumerate(sentences):
        score = 0.0
        if re.search(r"\d+", s):
            score += 2.0
        if '"' in s or "\u201c" in s:
            score += 1.5
        if 1 <= idx <= len(sentences) - 2:
            score += 0.5
        if len(s) < 50:
            score -= 2.0
        if len(s) >= 80:
            score += 1.0
        # Penalize fragments that start with lowercase (mid-sentence cuts)
        if s and s[0].islower():
            score -= 3.0
        scored.append((score, idx, s))

    scored.sort(key=lambda x: (-x[0], x[1]))

    details: list[str] = []
    used_words: set[str] = set()
    for _, _, s in scored:
        s_words = set(s.lower().split())
        if used_words:
            overlap = len(s_words & used_words) / max(len(s_words), 1)
            if overlap > 0.5:
                continue
        cleaned = _clean_detail(s)
        if cleaned:
            details.append(cleaned)
            used_words |= s_words
        if len(details) >= max_items:
            break

    return details


def _clean_detail(text: str) -> str:
    """Clean a key detail: strip wire prefixes, ensure natural ending."""
    text = _strip_wire_prefixes(text)
    shortened = _shorten(text, max_len=200)
    # If the shortened text doesn't end cleanly, trim to a natural break
    if shortened and shortened[-1] not in ".!?":
        # Try cutting at last comma or semicolon for a natural phrase boundary
        for sep in (",", ";"):
            last_sep = shortened.rfind(sep)
            if last_sep > len(shortened) // 3:
                shortened = shortened[:last_sep].rstrip() + "."
                break
        else:
            shortened = shortened.rstrip(" ,;:'\"")
            if shortened and shortened[-1] not in ".!?":
                shortened += "."
    # Strip leading/trailing quotes if unbalanced
    if shortened.startswith('"') and shortened.count('"') == 1:
        shortened = shortened[1:].lstrip()
    # Capitalize first letter if it starts lowercase
    if shortened and shortened[0].islower():
        shortened = shortened[0].upper() + shortened[1:]
    return shortened


def _find_by_keywords(
    sentences: list[str],
    keywords: frozenset[str],
    *,
    max_results: int = 1,
) -> list[str]:
    lower_kw = {k.lower() for k in keywords}
    results: list[str] = []
    for s in sentences:
        words = set(s.lower().split())
        if words & lower_kw:
            results.append(s)
            if len(results) >= max_results:
                break
    return results


def _extract_where_when(sentences: list[str], item: FeedItem) -> str:
    parts: list[str] = []
    if item.published_at:
        parts.append(item.published_at)
    if item.source_domain:
        parts.append(item.source_domain)
    for s in sentences:
        if any(kw in s.lower() for kw in ("today", "yesterday", "monday", "tuesday",
                "wednesday", "thursday", "friday", "saturday", "sunday",
                "오늘", "어제", "일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일")):
            parts.append(s)
            break
    return " | ".join(parts) if parts else "Details pending"


def _extract_tags(text: str, *, max_tags: int = 8) -> list[str]:
    words = re.findall(r"[a-zA-Z\uac00-\ud7a3]{2,}", text.lower())
    filtered = [w for w in words if w not in _STOPWORDS_EN and w not in _STOPWORDS_KO]
    counts = Counter(filtered)
    return [tag for tag, _ in counts.most_common(max_tags)]
