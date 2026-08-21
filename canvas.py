"""Shared drawing helpers for @tintix.lab palette cards."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

import config
from colors import (
    muted_text_color_for_background,
    normalize_hex,
    parse_hex,
    text_color_for_background,
)
from fonts_loader import load_arial_font, load_bold_font, load_font
from gemini_client import Band, Palette


def band_rects(width: int, height: int) -> list[tuple[int, int, int, int]]:
    band_height = height // 3
    return [
        (0, i * band_height, width, (i + 1) * band_height)
        for i in range(3)
    ]


def new_band_canvas(palette: Palette, size: tuple[int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw, list[tuple[int, int, int, int]]]:
    width, height = size
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    rects = band_rects(width, height)
    for band, rect in zip(palette.bands, rects):
        draw.rectangle(rect, fill=parse_hex(band.hex))
    return image, draw, rects


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    center_y: int,
    font,
    fill: tuple[int, int, int],
    stroke_width: int = 0,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        (center_x - text_w // 2, center_y - text_h // 2),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=fill,
    )


def _text_width_with_tracking(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    tracking: int,
    stroke_width: int = 0,
) -> int:
    if not text:
        return 0
    width = 0
    for i, char in enumerate(text):
        bbox = draw.textbbox((0, 0), char, font=font, stroke_width=stroke_width)
        width += bbox[2] - bbox[0]
        if i < len(text) - 1:
            width += tracking
    return width


def _draw_text_with_tracking(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font,
    fill: tuple[int, int, int],
    tracking: int,
    stroke_width: int = 0,
) -> None:
    cursor_x = x
    for i, char in enumerate(text):
        bbox = draw.textbbox((0, 0), char, font=font, stroke_width=stroke_width)
        draw.text(
            (cursor_x, y),
            char,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=fill,
        )
        cursor_x += (bbox[2] - bbox[0]) + (tracking if i < len(text) - 1 else 0)


def band_typography(height: int) -> tuple[int, int, int]:
    """Return title, hex, and header font sizes for a canvas height."""
    title_size = max(28, int(height * config.TITLE_FONT_RATIO))
    hex_size = max(14, int(height * config.HEX_FONT_RATIO))
    header_size = max(14, int(height * config.HEADER_FONT_RATIO))
    return title_size, hex_size, header_size


def draw_band_content(
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

    title_font = load_bold_font(title_size)
    hex_font = load_arial_font(hex_size)
    hex_text = f"HEX: {bg_hex.lower()}"

    title_bbox = draw.textbbox((0, 0), band.name, font=title_font)
    hex_bbox = draw.textbbox((0, 0), hex_text, font=hex_font)

    title_h = title_bbox[3] - title_bbox[1]
    hex_h = hex_bbox[3] - hex_bbox[1]
    gap = int(hex_size * config.NAME_HEX_GAP_RATIO)

    block_h = title_h + gap + hex_h
    block_top = center_y - block_h // 2

    title_x = center_x - (title_bbox[2] - title_bbox[0]) // 2
    title_y = block_top - title_bbox[1]
    draw.text((title_x, title_y), band.name, font=title_font, fill=title_color)

    hex_x = center_x - (hex_bbox[2] - hex_bbox[0]) // 2
    hex_y = block_top + title_h + gap - hex_bbox[1]
    draw.text((hex_x, hex_y), hex_text, font=hex_font, fill=hex_color)


def draw_top_header(
    draw: ImageDraw.ImageDraw,
    palette: Palette,
    size: tuple[int, int],
    rects: list[tuple[int, int, int, int]],
) -> None:
    width, height = size
    edge_pad = int(width * config.EDGE_PADDING_RATIO)
    header_offset = int(height * config.BAND_HEADER_OFFSET_RATIO)
    header_size = max(14, int(height * config.HEADER_FONT_RATIO))
    header_font = load_font(header_size)
    header_color = text_color_for_background(normalize_hex(palette.bands[0].hex))
    tracking = max(1, int(header_size * config.BRAND_HANDLE_TRACKING_RATIO))
    stroke_width = 1

    handle_w = _text_width_with_tracking(
        draw,
        config.BRAND_HANDLE,
        header_font,
        tracking,
        stroke_width=stroke_width,
    )
    handle_x = width - edge_pad - handle_w
    handle_y = rects[0][1] + header_offset
    _draw_text_with_tracking(
        draw,
        config.BRAND_HANDLE,
        handle_x,
        handle_y,
        header_font,
        header_color,
        tracking,
        stroke_width=stroke_width,
    )


def save_image(image: Image.Image, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path


def render_palette_card(palette: Palette, size: tuple[int, int]) -> Image.Image:
    """Render a full palette card with header and all band content."""
    _, height = size
    image, draw, rects = new_band_canvas(palette, size)
    draw_top_header(draw, palette, size, rects)
    title_size, hex_size, _header_size = band_typography(height)
    for band, rect in zip(palette.bands, rects):
        draw_band_content(draw, band, rect, title_size, hex_size)
    return image
