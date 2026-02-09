"""PIL drawing primitives for card rendering."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from auto_card_news_v2.render.theme import Color, Theme
from auto_card_news_v2.render.typography import load_font, text_height, wrap_text


def create_card_image(theme: Theme) -> Image.Image:
    """Create a new card image with gradient background."""
    img = Image.new("RGB", (theme.width, theme.height), theme.bg_top)
    _apply_gradient(img, theme.bg_top, theme.bg_bottom)
    return img


def _apply_gradient(img: Image.Image, top: Color, bottom: Color) -> None:
    """Apply vertical gradient from top to bottom color."""
    width, height = img.size
    pixels = img.load()
    for y in range(height):
        ratio = y / max(height - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        for x in range(width):
            pixels[x, y] = (r, g, b)  # type: ignore[index]


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    fill: Color | None = None,
    outline: Color | None = None,
    radius: int = 18,
) -> None:
    """Draw a rounded rectangle."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def draw_accent_line(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    color: Color,
    thickness: int = 3,
) -> None:
    """Draw a horizontal accent line."""
    draw.rectangle([x, y, x + width, y + thickness], fill=color)


def measure_text_block(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    line_spacing: int = 8,
) -> tuple[list[str], int]:
    """Measure wrapped text total height. Returns (lines, total_height)."""
    lines = wrap_text(text, font, max_width)
    total = 0
    for line in lines:
        total += text_height(font, line or "A") + line_spacing
    return lines, total


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
    color: Color,
    line_spacing: int = 8,
) -> int:
    """Draw wrapped text and return the Y position after the last line."""
    lines = wrap_text(text, font, max_width)
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += text_height(font, line or "A") + line_spacing
    return current_y


def draw_header(
    draw: ImageDraw.ImageDraw,
    theme: Theme,
    *,
    source: str,
    date: str,
    position: str,
) -> None:
    """Draw the header bar with source, date, and card position."""
    font = load_font(30)
    margin = theme.margin
    y = margin

    draw.text((margin, y), source, font=font, fill=theme.text_muted)

    pos_bbox = font.getbbox(position)
    pos_width = pos_bbox[2] - pos_bbox[0]
    draw.text((theme.width - margin - pos_width, y), position, font=font, fill=theme.accent)

    if date:
        date_bbox = font.getbbox(date)
        date_width = date_bbox[2] - date_bbox[0]
        center_x = (theme.width - date_width) // 2
        draw.text((center_x, y), date, font=font, fill=theme.text_muted)


def draw_footer(
    draw: ImageDraw.ImageDraw,
    theme: Theme,
    *,
    text: str,
) -> None:
    """Draw footer text at the bottom of the card."""
    font = load_font(28)
    margin = theme.margin
    y = theme.height - theme.footer_height + 20

    draw_accent_line(draw, margin, y - 15, theme.width - 2 * margin, theme.border, 1)
    draw.text((margin, y), text, font=font, fill=theme.text_muted)
