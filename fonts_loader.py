"""Load Foda Display for all @tintix.lab typography."""

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


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _foda_candidates():
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    raise FileNotFoundError(
        "Foda Display font not found. Place the licensed .otf or .ttf file in the fonts/ folder."
    )
