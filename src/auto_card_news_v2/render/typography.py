"""Font loading and text wrapping utilities."""

from __future__ import annotations

import unicodedata

from PIL import ImageFont

_FONT_CANDIDATES = [
    "AppleSDGothicNeo-Medium",
    "AppleSDGothicNeo",
    "AppleGothic",
    "NanumGothic",
    "NotoSansKR-Regular",
    "NotoSansCJKkr-Regular",
    "DejaVuSans",
    "Arial",
]

_BOLD_CANDIDATES = [
    "AppleSDGothicNeo-Bold",
    "NanumGothicBold",
    "NotoSansKR-Bold",
    "NotoSansCJKkr-Bold",
    "DejaVuSans-Bold",
    "Arial Bold",
]

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font with Korean support, falling back through candidates."""
    candidates = _BOLD_CANDIDATES if bold else _FONT_CANDIDATES
    cache_key = ("bold" if bold else "regular", size)

    if cache_key in _font_cache:
        return _font_cache[cache_key]

    for name in candidates:
        try:
            font = ImageFont.truetype(name, size)
            _font_cache[cache_key] = font
            return font
        except (OSError, IOError):
            continue

    font = ImageFont.load_default()
    return font  # type: ignore[return-value]


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    if not text:
        return []

    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        wrapped = _wrap_paragraph(paragraph, font, max_width)
        lines.extend(wrapped)
    return lines


def _wrap_paragraph(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip() if current else word
        bbox = font.getbbox(test)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            if _has_cjk(word) and _text_width(font, word) > max_width:
                lines.extend(_wrap_by_chars(word, font, max_width))
                current = ""
            else:
                current = word

    if current:
        lines.append(current)
    return lines if lines else [""]


def _wrap_by_chars(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        test = current + ch
        if _text_width(font, test) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def _text_width(font: ImageFont.FreeTypeFont, text: str) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def text_height(font: ImageFont.FreeTypeFont, text: str) -> int:
    bbox = font.getbbox(text)
    return bbox[3] - bbox[1]


def _has_cjk(text: str) -> bool:
    return any(
        unicodedata.category(ch).startswith("Lo") and ord(ch) > 0x2E80
        for ch in text
    )
