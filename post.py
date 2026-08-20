"""Instagram Post (1080×1080) generator for @tintix.lab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import config
from canvas import save_palette_image
from gemini_client import Palette


def generate_post(
    palette: Palette,
    output_dir: Path | str = config.OUTPUT_DIR,
    filename: str | None = None,
) -> Path:
    """Render and save a square Instagram Post palette card."""
    out = Path(output_dir)
    name = filename or f"post_{datetime.now():%Y%m%d_%H%M%S}.png"
    return save_palette_image(palette, config.POST_SIZE, out / name)
