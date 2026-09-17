"""Color parsing and contrast utilities."""

from __future__ import annotations

import math
import re
from typing import Tuple

HexColor = str
RGB = Tuple[int, int, int]
LAB = Tuple[float, float, float]


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


def _mix(a: RGB, b: RGB, t: float) -> RGB:
    return (
        int(a[0] * (1 - t) + b[0] * t),
        int(a[1] * (1 - t) + b[1] * t),
        int(a[2] * (1 - t) + b[2] * t),
    )


def _band_tinted_dark_text(rgb: RGB, strength: float = 0.32) -> RGB:
    """Derive a readable dark text color that keeps each band's hue."""
    espresso = (42, 32, 30)
    band_dark = (
        max(18, int(rgb[0] * strength)),
        max(16, int(rgb[1] * strength)),
        max(14, int(rgb[2] * strength)),
    )
    return _mix(espresso, band_dark, 0.55)


def text_color_for_background(hex_color: str) -> RGB:
    """
    Pick editorial text color with strong contrast against the band background.
    Light pastels → band-tinted deep brown; dark tones → warm off-white.
    """
    rgb = parse_hex(hex_color)
    lum = relative_luminance(rgb)
    if lum > 0.55:
        return _band_tinted_dark_text(rgb, strength=0.30)
    if lum > 0.35:
        return _band_tinted_dark_text(rgb, strength=0.38)
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


def _srgb_to_linear(c: float) -> float:
    """Convert sRGB channel (0-1) to linear RGB."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _xyz_to_lab_f(t: float) -> float:
    """CIE LAB transfer function."""
    delta = 6.0 / 29.0
    if t > delta ** 3:
        return t ** (1.0 / 3.0)
    return t / (3.0 * delta ** 2) + 4.0 / 29.0


def rgb_to_lab(rgb: RGB) -> LAB:
    """
    Convert RGB to CIELAB color space.
    Uses D65 illuminant (standard daylight).
    """
    r, g, b = rgb
    r_lin = _srgb_to_linear(r / 255.0)
    g_lin = _srgb_to_linear(g / 255.0)
    b_lin = _srgb_to_linear(b / 255.0)

    x = 0.4124564 * r_lin + 0.3575761 * g_lin + 0.1804375 * b_lin
    y = 0.2126729 * r_lin + 0.7151522 * g_lin + 0.0721750 * b_lin
    z = 0.0193339 * r_lin + 0.1191920 * g_lin + 0.9503041 * b_lin

    x_n, y_n, z_n = 0.95047, 1.00000, 1.08883

    f_x = _xyz_to_lab_f(x / x_n)
    f_y = _xyz_to_lab_f(y / y_n)
    f_z = _xyz_to_lab_f(z / z_n)

    L = 116.0 * f_y - 16.0
    a = 500.0 * (f_x - f_y)
    b_val = 200.0 * (f_y - f_z)

    return (L, a, b_val)


def delta_e_cie76(lab1: LAB, lab2: LAB) -> float:
    """
    Calculate Delta E (CIE76) - Euclidean distance in LAB space.
    Values < 1: imperceptible difference
    Values 1-2: perceptible through close observation
    Values 2-10: perceptible at a glance
    Values 11-49: colors are more similar than opposite
    Values 100: colors are exact opposites
    """
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL * dL + da * da + db * db)


def hex_to_lab(hex_color: str) -> LAB:
    """Convenience function: hex string to LAB."""
    return rgb_to_lab(parse_hex(hex_color))
