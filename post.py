#!/usr/bin/env python3
"""Instagram Post (1080×1080) generator for @tintix.lab."""

from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

import canvas
import config
from gemini_client import Palette, sample_palette
from instagram_client import publish_to_instagram
from palette_pool import advance_after_publish, get_next_palette

SIZE = config.POST_SIZE


def render_post(palette: Palette) -> Image.Image:
    """Render a 1080×1080 Instagram Post palette card."""
    _, height = SIZE
    image, draw, rects = canvas.new_band_canvas(palette, SIZE)
    canvas.draw_top_header(draw, palette, SIZE, rects)

    title_size = max(28, int(height * config.TITLE_FONT_RATIO))
    hex_size = max(14, int(height * config.HEX_FONT_RATIO))
    for band, rect in zip(palette.bands, rects):
        canvas.draw_band_content(draw, band, rect, title_size, hex_size)

    return image


def generate_post(
    palette: Palette,
    output_dir: Path | str,
    filename: str | None = None,
) -> Path:
    """Render and save a square Instagram Post palette card."""
    name = filename or f"post_{datetime.now():%Y%m%d_%H%M%S}.png"
    return canvas.save_image(render_post(palette), Path(output_dir) / name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and publish an @tintix.lab Instagram Post.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use built-in sample palette (no Gemini API call)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Gemini model override (default: auto fallback chain)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)

    try:
        if args.sample:
            palette = sample_palette()
            palette_index = None
        else:
            palette, palette_index, _cycle = get_next_palette("post")
    except EnvironmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Tip: run with --sample to test locally without an API key.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed to load palette: {exc}", file=sys.stderr)
        return 1

    print(f"Theme: {palette.theme}")
    for i, band in enumerate(palette.bands, 1):
        print(f"  Band {i}: {band.name} — {band.hex}")
    print(f"\nCaption:\n{palette.caption}\n")

    with tempfile.TemporaryDirectory(prefix="tintix-post-") as tmp:
        post_path = generate_post(palette, Path(tmp))
        print(f"Generated post: {post_path.name}")

        try:
            results = publish_to_instagram(
                post_path=post_path,
                story_path=None,
                caption=palette.caption,
                publish_post=True,
                publish_story=False,
            )
            for kind, media_id in results.items():
                print(f"Published {kind}: media_id={media_id}")
            if palette_index is not None:
                advance_after_publish("post", palette_index)
        except Exception as exc:
            print(f"Instagram publish failed: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
