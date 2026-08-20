"""Color parsing and contrast utilities."""

from __future__ import annotations

import re
from typing import Tuple

HexColor = str
RGB = Tuple[int, int, int]


def parse_hex(hex_color: str) -> RGB:
    """Parse #RRGGBB or RRGGBB into an (r, g, b) tuple."""
    cleaned = hex_color.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", cleaned):
        raise ValueError(f"Invalid hex color: {hex_color}")
    return (
        int(cleaned[0:2], 16),
        int(cleaned[2:4], 16),
        int(cleaned[4:6], 16),
    )


def normalize_hex(hex_color: str) -> str:
    r, g, b = parse_hex(hex_color)
    return f"#{r:02x}{g:02x}{b:02x}"


def relative_luminance(rgb: RGB) -> float:
    """WCAG relative luminance for sRGB."""
    def channel(value: int) -> float:
        c = value / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def text_color_for_background(hex_color: str) -> RGB:
    """
    Pick editorial text color with strong contrast against the band background.
    Light pastels → deep espresso brown; dark tones → warm off-white.
    """
    lum = relative_luminance(parse_hex(hex_color))
    if lum > 0.55:
        return (42, 32, 30)  # espresso brown
    if lum > 0.35:
        return (58, 46, 42)
    return (245, 240, 235)  # warm off-white


def muted_text_color_for_background(hex_color: str) -> RGB:
    """Slightly softer variant for secondary lines (hex labels)."""
    base = text_color_for_background(hex_color)
    lum = relative_luminance(parse_hex(hex_color))
    if lum > 0.55:
        r, g, b = base
        return (min(255, r + 35), min(255, g + 30), min(255, b + 28))
    r, g, b = base
    return (max(0, r - 25), max(0, g - 25), max(0, b - 25))
