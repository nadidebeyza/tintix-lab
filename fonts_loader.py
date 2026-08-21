"""Load Foda Display, bold display, and Arial for @tintix.lab typography."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import ImageFont

BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "fonts"

FODA_DISPLAY_CANDIDATES = [
    FONTS_DIR / "FodaDisplay-Regular.otf",
    FONTS_DIR / "FodaDisplay-Regular.ttf",
    FONTS_DIR / "Foda Display Regular.otf",
    FONTS_DIR / "Foda Display Regular.ttf",
    FONTS_DIR / "FodaDisplay.otf",
    FONTS_DIR / "FodaDisplay.ttf",
    FONTS_DIR / "font-display.ttf",
    BASE_DIR / "FodaDisplay-Regular.otf",
    BASE_DIR / "Foda Display Regular.otf",
    BASE_DIR / "font-display.ttf",
]

FODA_BOLD_CANDIDATES = [
    FONTS_DIR / "FodaDisplay-Bold.otf",
    FONTS_DIR / "FodaDisplay-Bold.ttf",
    FONTS_DIR / "Foda Display Bold.otf",
    FONTS_DIR / "Foda Display Bold.ttf",
    BASE_DIR / "FodaDisplay-Bold.otf",
    BASE_DIR / "Foda Display Bold.otf",
    # Same display face as regular when no separate bold file is bundled (sentiment-club pattern)
    FONTS_DIR / "FodaDisplay-Regular.ttf",
    FONTS_DIR / "font-display.ttf",
    BASE_DIR / "font-display.ttf",
]

if sys.platform == "darwin":
    ARIAL_CANDIDATES = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    ]
    DISPLAY_FALLBACK_CANDIDATES = [
        Path("/System/Library/Fonts/Supplemental/Didot.ttc"),
        Path("/System/Library/Fonts/Supplemental/Georgia.ttf"),
    ]
    BOLD_FALLBACK_CANDIDATES = [
        Path("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ]
elif sys.platform.startswith("linux"):
    ARIAL_CANDIDATES = [
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    DISPLAY_FALLBACK_CANDIDATES = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
    ]
    BOLD_FALLBACK_CANDIDATES = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]
else:
    ARIAL_CANDIDATES = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/Arial.ttf"),
    ]
    DISPLAY_FALLBACK_CANDIDATES = [
        Path("C:/Windows/Fonts/georgia.ttf"),
    ]
    BOLD_FALLBACK_CANDIDATES = [
        Path("C:/Windows/Fonts/georgiab.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]

_warned_fallback = False


def _discovered_foda_regular() -> list[Path]:
    found: list[Path] = []
    if FONTS_DIR.exists():
        for path in sorted(FONTS_DIR.iterdir()):
            name = path.name.lower()
            if path.suffix.lower() in {".otf", ".ttf"} and "foda" in name and "bold" not in name:
                found.append(path)
    return found


def _discovered_foda_bold() -> list[Path]:
    found: list[Path] = []
    if FONTS_DIR.exists():
        for path in sorted(FONTS_DIR.iterdir()):
            name = path.name.lower()
            if path.suffix.lower() in {".otf", ".ttf"} and "foda" in name and "bold" in name:
                found.append(path)
    return found


def _foda_regular_candidates() -> list[Path]:
    env_path = os.getenv("FODA_DISPLAY_FONT_PATH", "").strip()
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(_discovered_foda_regular())
    for path in FODA_DISPLAY_CANDIDATES:
        if path not in candidates:
            candidates.append(path)
    if sys.platform == "darwin":
        candidates.extend([
            Path.home() / "Library/Fonts/Foda Display Regular.otf",
            Path.home() / "Library/Fonts/FodaDisplay-Regular.otf",
            Path("/Library/Fonts/Foda Display Regular.otf"),
            Path("/Library/Fonts/FodaDisplay-Regular.otf"),
        ])
    elif sys.platform.startswith("linux"):
        candidates.extend([
            Path.home() / ".local/share/fonts/FodaDisplay-Regular.otf",
            Path("/usr/local/share/fonts/FodaDisplay-Regular.otf"),
        ])
    return candidates


def _foda_bold_candidates() -> list[Path]:
    candidates = _discovered_foda_bold()
    for path in FODA_BOLD_CANDIDATES:
        if path not in candidates:
            candidates.append(path)
    return candidates


def _try_load(path: Path, size: int) -> ImageFont.FreeTypeFont | None:
    if not path.exists():
        return None
    try:
        return ImageFont.truetype(str(path), size=size)
    except OSError:
        return None


def _load_first(candidates: list[Path], size: int) -> ImageFont.FreeTypeFont | None:
    for path in candidates:
        font = _try_load(path, size)
        if font is not None:
            return font
    return None


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Foda Display regular — used for @tintix.lab handle."""
    global _warned_fallback

    font = _load_first(_foda_regular_candidates(), size)
    if font is not None:
        return font

    font = _load_first(DISPLAY_FALLBACK_CANDIDATES, size)
    if font is not None:
        if not _warned_fallback:
            print(
                "Note: Foda Display not found — using system display fallback. "
                "Add FodaDisplay-Regular.otf to fonts/ for brand typography."
            )
            _warned_fallback = True
        return font

    return ImageFont.load_default()


def load_bold_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Foda Display bold for color names; falls back to Foda regular before system bold."""
    font = _load_first(_foda_bold_candidates(), size)
    if font is not None:
        return font

    font = _load_first(_foda_regular_candidates(), size)
    if font is not None:
        return font

    font = _load_first(BOLD_FALLBACK_CANDIDATES, size)
    if font is not None:
        return font

    return load_font(size)


def load_arial_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Arial (or Liberation Sans on Linux) for HEX lines."""
    font = _load_first(ARIAL_CANDIDATES, size)
    if font is not None:
        return font
    return load_font(size)
