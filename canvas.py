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
from fonts_loader import load_font
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
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((center_x - text_w // 2, center_y - text_h // 2), text, font=font, fill=fill)


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

    title_font = load_font(title_size)
    hex_font = load_font(hex_size)

    title_bbox = draw.textbbox((0, 0), band.name, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]
    gap = int(hex_size * 0.6)

    draw_centered_text(
        draw,
        band.name,
        center_x,
        center_y - gap - title_h // 2,
        title_font,
        title_color,
    )
    draw_centered_text(
        draw,
        f"HEX: {bg_hex.lower()}",
        center_x,
        center_y + gap + hex_size // 2,
        hex_font,
        hex_color,
    )


def draw_top_header(
    draw: ImageDraw.ImageDraw,
    palette: Palette,
    size: tuple[int, int],
    rects: list[tuple[int, int, int, int]],
    header_left: str | None = None,
) -> None:
    width, height = size
    edge_pad = int(width * config.EDGE_PADDING_RATIO)
    header_offset = int(height * config.BAND_HEADER_OFFSET_RATIO)
    header_size = max(14, int(height * config.HEADER_FONT_RATIO))
    header_font = load_font(header_size)
    header_color = text_color_for_background(normalize_hex(palette.bands[0].hex))
    left_header = header_left or config.HEADER_LEFT

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


def save_image(image: Image.Image, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path
