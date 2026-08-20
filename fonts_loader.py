"""Font loading with graceful fallbacks for editorial typography."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

FONTS_DIR = Path(__file__).parent / "fonts"

# macOS system font candidates
SANS_LIGHT_CANDIDATES = [
    FONTS_DIR / "Inter-Light.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

SERIF_BOLD_CANDIDATES = [
    FONTS_DIR / "PlayfairDisplay-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/Library/Fonts/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
]

SANS_REGULAR_CANDIDATES = [
    FONTS_DIR / "Inter-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _load_first_available(candidates: list, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def load_sans_light(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _load_first_available(SANS_LIGHT_CANDIDATES, size)


def load_sans_regular(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _load_first_available(SANS_REGULAR_CANDIDATES, size)


def load_serif_bold(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _load_first_available(SERIF_BOLD_CANDIDATES, size)
