"""Load Foda Display for all @tintix.lab typography, with system fallbacks."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

FONTS_DIR = Path(__file__).parent / "fonts"

FODA_DISPLAY_CANDIDATES = [
    FONTS_DIR / "FodaDisplay-Regular.otf",
    FONTS_DIR / "FodaDisplay-Regular.ttf",
    FONTS_DIR / "Foda Display Regular.otf",
    FONTS_DIR / "Foda Display Regular.ttf",
    FONTS_DIR / "FodaDisplay.otf",
    FONTS_DIR / "FodaDisplay.ttf",
    FONTS_DIR / "Foda-Display.otf",
    FONTS_DIR / "Foda-Display.ttf",
]

FALLBACK_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Didot.ttc"),
    Path("/System/Library/Fonts/Supplemental/Georgia.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
]

BOLD_CANDIDATES = [
    FONTS_DIR / "FodaDisplay-Bold.otf",
    FONTS_DIR / "FodaDisplay-Bold.ttf",
    FONTS_DIR / "Foda Display Bold.otf",
    FONTS_DIR / "Foda Display Bold.ttf",
    Path("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
]

ARIAL_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
]

_warned_fallback = False


def _foda_candidates() -> list[Path]:
    found: list[Path] = []
    if FONTS_DIR.exists():
        for path in sorted(FONTS_DIR.iterdir()):
            if path.suffix.lower() in {".otf", ".ttf"} and "foda" in path.name.lower():
                found.append(path)
    for path in FODA_DISPLAY_CANDIDATES:
        if path not in found:
            found.append(path)
    return found


def _try_load(path: Path, size: int) -> ImageFont.FreeTypeFont | None:
    if not path.exists():
        return None
    try:
        return ImageFont.truetype(str(path), size=size)
    except OSError:
        return None


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    global _warned_fallback

    for path in _foda_candidates():
        font = _try_load(path, size)
        if font is not None:
            return font

    for path in FALLBACK_CANDIDATES:
        font = _try_load(path, size)
        if font is not None:
            if not _warned_fallback:
                print(
                    "Note: Foda Display not found in fonts/; using a system fallback. "
                    "Add the licensed .otf/.ttf to fonts/ to use Foda Display."
                )
                _warned_fallback = True
            return font

    return ImageFont.load_default()


def load_bold_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if FONTS_DIR.exists():
        for path in sorted(FONTS_DIR.iterdir()):
            name = path.name.lower()
            if path.suffix.lower() in {".otf", ".ttf"} and "foda" in name and "bold" in name:
                font = _try_load(path, size)
                if font is not None:
                    return font

    for path in BOLD_CANDIDATES:
        font = _try_load(path, size)
        if font is not None:
            return font

    return load_font(size)


def load_arial_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in ARIAL_CANDIDATES:
        font = _try_load(path, size)
        if font is not None:
            return font
    return ImageFont.load_default()
