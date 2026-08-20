"""Instagram Story (1080×1920) generator for @tintix.lab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import config
from canvas import save_palette_image
from gemini_client import Palette


def generate_story(
    palette: Palette,
    output_dir: Path | str = config.OUTPUT_DIR,
    filename: str | None = None,
) -> Path:
    """Render and save an Instagram Story palette card."""
    out = Path(output_dir)
    name = filename or f"story_{datetime.now():%Y%m%d_%H%M%S}.png"
    return save_palette_image(palette, config.STORY_SIZE, out / name)
