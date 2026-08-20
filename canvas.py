"""Core 3-band palette canvas renderer for @tintix.lab."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

import config
from colors import (
    muted_text_color_for_background,
    normalize_hex,
    parse_hex,
    text_color_for_background,
)
from fonts_loader import load_sans_light, load_sans_regular, load_serif_bold
from gemini_client import Band, Palette


def _band_rects(width: int, height: int) -> list[tuple[int, int, int, int]]:
    band_height = height // 3
    return [
        (0, i * band_height, width, (i + 1) * band_height)
        for i in range(3)
    ]


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    center_y: int,
    font,
    fill: tuple[int, int, int],
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((center_x - text_w // 2, center_y - text_h // 2), text, font=font, fill=fill)


def _draw_band_content(
    draw: ImageDraw.ImageDraw,
    band: Band,
    rect: tuple[int, int, int, int],
    title_size: int,
    hex_size: int,
) -> None:
    x0, y0, x1, y1 = rect
    center_x = (x0 + x1) // 2
    center_y = (y0 + y1) // 2

    bg_hex = normalize_hex(band.hex)
    title_color = text_color_for_background(bg_hex)
    hex_color = muted_text_color_for_background(bg_hex)

    title_font = load_serif_bold(title_size)
    hex_font = load_sans_regular(hex_size)

    title_bbox = draw.textbbox((0, 0), band.name, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]
    gap = int(hex_size * 0.35)

    _draw_centered_text(
        draw,
        band.name,
        center_x,
        center_y - gap - title_h // 2,
        title_font,
        title_color,
    )
    _draw_centered_text(
        draw,
        f"tint {bg_hex.lower()}",
        center_x,
        center_y + gap + hex_size // 2,
        hex_font,
        hex_color,
    )


def render_palette(
    palette: Palette,
    size: tuple[int, int],
    header_left: str | None = None,
) -> Image.Image:
    """Render a 3-band vertical palette card."""
    width, height = size
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    rects = _band_rects(width, height)
    for band, rect in zip(palette.bands, rects):
        draw.rectangle(rect, fill=parse_hex(band.hex))

    edge_pad = int(width * config.EDGE_PADDING_RATIO)
    header_offset = int(height * config.BAND_HEADER_OFFSET_RATIO)
    footer_offset = int(height * config.BAND_FOOTER_OFFSET_RATIO)

    header_size = max(14, int(height * config.HEADER_FONT_RATIO))
    footer_size = max(12, int(height * config.FOOTER_FONT_RATIO))
    title_size = max(28, int(height * config.TITLE_FONT_RATIO))
    hex_size = max(14, int(height * config.HEX_FONT_RATIO))

    header_font = load_sans_light(header_size)
    footer_font = load_sans_light(footer_size)

    top_band_hex = normalize_hex(palette.bands[0].hex)
    bottom_band_hex = normalize_hex(palette.bands[2].hex)
    header_color = text_color_for_background(top_band_hex)
    footer_color = text_color_for_background(bottom_band_hex)

    left_header = header_left or random.choice(config.HEADER_LEFT_OPTIONS)

    # Top header row (over band 1)
    draw.text(
        (edge_pad, rects[0][1] + header_offset),
        left_header,
        font=header_font,
        fill=header_color,
    )
    handle_bbox = draw.textbbox((0, 0), config.BRAND_HANDLE, font=header_font)
    handle_w = handle_bbox[2] - handle_bbox[0]
    draw.text(
        (width - edge_pad - handle_w, rects[0][1] + header_offset),
        config.BRAND_HANDLE,
        font=header_font,
        fill=header_color,
    )

    # Center content per band
    for band, rect in zip(palette.bands, rects):
        _draw_band_content(draw, band, rect, title_size, hex_size)

    # Bottom footer row (over band 3)
    footer_y = rects[2][3] - footer_offset - footer_size
    draw.text(
        (edge_pad, footer_y),
        config.FOOTER_LEFT,
        font=footer_font,
        fill=footer_color,
    )
    footer_handle_bbox = draw.textbbox((0, 0), config.BRAND_HANDLE, font=footer_font)
    footer_handle_w = footer_handle_bbox[2] - footer_handle_bbox[0]
    draw.text(
        (width - edge_pad - footer_handle_w, footer_y),
        config.BRAND_HANDLE,
        font=footer_font,
        fill=footer_color,
    )

    return image


def save_palette_image(
    palette: Palette,
    size: tuple[int, int],
    output_path: Path,
    header_left: str | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = render_palette(palette, size, header_left=header_left)
    image.save(output_path, format="PNG", optimize=True)
    return output_path
