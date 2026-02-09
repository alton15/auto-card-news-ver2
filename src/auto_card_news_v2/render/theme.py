"""Color and dimension theme configuration for card rendering."""

from __future__ import annotations

from dataclasses import dataclass

# RGB tuples for PIL compatibility
Color = tuple[int, int, int]


def _rgb(c: Color) -> str:
    """Convert RGB tuple to CSS rgb() string."""
    return f"rgb({c[0]}, {c[1]}, {c[2]})"


def _rgba(c: Color, a: float) -> str:
    """Convert RGB tuple to CSS rgba() string."""
    return f"rgba({c[0]}, {c[1]}, {c[2]}, {a})"


@dataclass(frozen=True)
class Theme:
    """Visual theme for card rendering."""

    width: int = 1080
    height: int = 1350
    margin: int = 70

    bg_top: Color = (15, 23, 42)
    bg_bottom: Color = (15, 23, 42)
    surface: Color = (30, 41, 59)
    border: Color = (51, 65, 85)
    accent: Color = (56, 189, 248)
    accent2: Color = (139, 92, 246)
    text_primary: Color = (255, 255, 255)
    text_secondary: Color = (203, 213, 225)
    text_muted: Color = (100, 116, 139)

    header_height: int = 120
    footer_height: int = 140
    box_radius: int = 18

    font_heading: str = "Inter"
    font_body: str = "Inter"
    font_kr: str = "Noto Sans KR"
    font_import: str = (
        "https://fonts.googleapis.com/css2?"
        "family=Inter:wght@300;400;500;600;700;800;900"
        "&family=Noto+Sans+KR:wght@400;600;700"
        "&display=swap"
    )

    bg_gradient_css: str = ""

    @classmethod
    def light(cls) -> Theme:
        return cls(
            bg_top=(248, 250, 252),
            bg_bottom=(226, 232, 240),
            surface=(255, 255, 255),
            border=(203, 213, 225),
            accent=(14, 165, 233),
            accent2=(99, 102, 241),
            text_primary=(15, 23, 42),
            text_secondary=(51, 65, 85),
            text_muted=(100, 116, 139),
        )

    @classmethod
    def dark(cls) -> Theme:
        return cls()

    @classmethod
    def modern_bold(cls) -> Theme:
        """Deep indigo/purple gradient + bold geometric headings."""
        return cls(
            bg_top=(25, 15, 60),
            bg_bottom=(10, 8, 35),
            surface=(40, 30, 80),
            border=(60, 45, 100),
            accent=(167, 139, 250),
            accent2=(236, 72, 153),
            text_primary=(255, 255, 255),
            text_secondary=(216, 210, 240),
            text_muted=(130, 120, 170),
            font_heading="Sora",
            font_body="DM Sans",
            font_kr="Noto Sans KR",
            font_import=(
                "https://fonts.googleapis.com/css2?"
                "family=Sora:wght@400;600;700;800"
                "&family=DM+Sans:wght@400;500;600;700"
                "&family=Noto+Sans+KR:wght@400;600;700"
                "&display=swap"
            ),
            bg_gradient_css=(
                "linear-gradient(145deg, "
                "rgb(30, 15, 70) 0%, "
                "rgb(20, 10, 50) 40%, "
                "rgb(10, 8, 35) 100%)"
            ),
        )

    @classmethod
    def clean_minimal(cls) -> Theme:
        """Light background, clean sans-serif, Apple-like."""
        return cls(
            bg_top=(250, 250, 252),
            bg_bottom=(240, 240, 245),
            surface=(255, 255, 255),
            border=(228, 228, 235),
            accent=(59, 130, 246),
            accent2=(99, 102, 241),
            text_primary=(17, 24, 39),
            text_secondary=(55, 65, 81),
            text_muted=(156, 163, 175),
            font_heading="Plus Jakarta Sans",
            font_body="Plus Jakarta Sans",
            font_kr="Noto Sans KR",
            font_import=(
                "https://fonts.googleapis.com/css2?"
                "family=Plus+Jakarta+Sans:wght@400;500;600;700;800"
                "&family=Noto+Sans+KR:wght@400;600;700"
                "&display=swap"
            ),
            bg_gradient_css=(
                "linear-gradient(180deg, "
                "rgb(250, 250, 252) 0%, "
                "rgb(240, 242, 248) 50%, "
                "rgb(235, 238, 245) 100%)"
            ),
        )


    @classmethod
    def vibrant_trendy(cls) -> Theme:
        """Colorful gradient background, rounded font, Instagram-like."""
        return cls(
            bg_top=(15, 20, 45),
            bg_bottom=(25, 10, 40),
            surface=(35, 30, 60),
            border=(60, 50, 90),
            accent=(0, 210, 190),
            accent2=(255, 100, 150),
            text_primary=(255, 255, 255),
            text_secondary=(210, 215, 230),
            text_muted=(130, 135, 160),
            font_heading="Outfit",
            font_body="Outfit",
            font_kr="Noto Sans KR",
            font_import=(
                "https://fonts.googleapis.com/css2?"
                "family=Outfit:wght@400;500;600;700;800;900"
                "&family=Noto+Sans+KR:wght@400;600;700"
                "&display=swap"
            ),
            bg_gradient_css=(
                "linear-gradient(135deg, "
                "rgb(20, 10, 55) 0%, "
                "rgb(15, 20, 50) 35%, "
                "rgb(10, 25, 45) 65%, "
                "rgb(20, 12, 45) 100%)"
            ),
        )

    def css_vars(self) -> dict[str, str]:
        """Return a dict of CSS template variables for Jinja2 rendering."""
        bg_grad = self.bg_gradient_css or (
            f"linear-gradient(160deg, "
            f"{_rgba(self.bg_top, 1)} 0%, "
            f"{_rgb(self.bg_bottom)} 100%)"
        )
        return {
            "bg": _rgb(self.bg_top),
            "surface": _rgba(self.surface, 0.80),
            "border": _rgba(self.border, 0.4),
            "accent": _rgb(self.accent),
            "accent_gradient": f"linear-gradient(135deg, {_rgb(self.accent)}, {_rgb(self.accent2)})",
            "title_gradient": f"linear-gradient(135deg, {_rgb(self.text_primary)} 0%, {_rgb(self.accent)} 100%)",
            "text_color": _rgb(self.text_primary),
            "text_secondary": _rgb(self.text_secondary),
            "text_muted": _rgb(self.text_muted),
            "cta_bg": f"linear-gradient(180deg, {_rgba(self.surface, 0.85)}, {_rgba(self.bg_bottom, 0.95)})",
            "bg_gradient": bg_grad,
            "font_heading": f"'{self.font_heading}'",
            "font_body": f"'{self.font_body}'",
            "font_kr": f"'{self.font_kr}'",
            "font_import": self.font_import,
        }
