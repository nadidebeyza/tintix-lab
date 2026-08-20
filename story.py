#!/usr/bin/env python3
"""Instagram Story (1080×1920) generator for @tintix.lab."""

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
from gemini_client import Palette, generate_palette, sample_palette
from instagram_client import publish_to_instagram

SIZE = config.STORY_SIZE


def render_story(palette: Palette) -> Image.Image:
    """Render a 1080×1920 Instagram Story palette card."""
    _, height = SIZE
    image, draw, rects = canvas.new_band_canvas(palette, SIZE)
    canvas.draw_top_header(draw, palette, SIZE, rects)

    title_size = max(28, int(height * config.TITLE_FONT_RATIO))
    hex_size = max(14, int(height * config.HEX_FONT_RATIO))
    for band, rect in zip(palette.bands, rects):
        canvas.draw_band_content(draw, band, rect, title_size, hex_size)

    return image


def generate_story(
    palette: Palette,
    output_dir: Path | str,
    filename: str | None = None,
) -> Path:
    """Render and save an Instagram Story palette card."""
    name = filename or f"story_{datetime.now():%Y%m%d_%H%M%S}.png"
    return canvas.save_image(render_story(palette), Path(output_dir) / name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and publish an @tintix.lab Instagram Story.",
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
        palette = sample_palette() if args.sample else generate_palette(model=args.model)
    except EnvironmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Tip: run with --sample to test locally without an API key.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed to generate palette: {exc}", file=sys.stderr)
        return 1

    print(f"Theme: {palette.theme}")
    for i, band in enumerate(palette.bands, 1):
        print(f"  Band {i}: {band.name} — {band.hex}")
    print(f"\nCaption:\n{palette.caption}\n")

    with tempfile.TemporaryDirectory(prefix="tintix-story-") as tmp:
        story_path = generate_story(palette, Path(tmp))
        print(f"Generated story: {story_path.name}")

        try:
            results = publish_to_instagram(
                post_path=None,
                story_path=story_path,
                caption=palette.caption,
                publish_post=False,
                publish_story=True,
            )
            for kind, media_id in results.items():
                print(f"Published {kind}: media_id={media_id}")
        except Exception as exc:
            print(f"Instagram publish failed: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
