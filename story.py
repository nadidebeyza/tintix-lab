#!/usr/bin/env python3
"""
@tintix.lab — Instagram Story automation pipeline.

Generates palette via Gemini, renders 1080×1920 card, hosts publicly,
and publishes to Instagram. Tracks last 30 story palettes in story_history.json.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

import canvas
import config
from gemini_client import Palette, generate_palette, sample_palette
from image_host import get_public_image_url
from instagram_client import InstagramClient
from instagram_setup import verify_instagram_setup
from main import _print_palette, build_parser
from palette_history import record_published_palette

OUTPUT_STORY = config.BASE_DIR / "final_story.png"


def render_story(palette: Palette) -> Path:
    _, height = config.STORY_SIZE
    image, draw, rects = canvas.new_band_canvas(palette, config.STORY_SIZE)
    canvas.draw_top_header(draw, palette, config.STORY_SIZE, rects)

    title_size = max(28, int(height * config.TITLE_FONT_RATIO))
    hex_size = max(14, int(height * config.HEX_FONT_RATIO))
    for band, rect in zip(palette.bands, rects):
        canvas.draw_band_content(draw, band, rect, title_size, hex_size)

    return canvas.save_image(image, OUTPUT_STORY)


def run_story_pipeline(*, sample: bool = False, model: str | None = None) -> None:
    verify_instagram_setup()

    if sample:
        palette = sample_palette()
    else:
        palette = generate_palette("story", model=model)

    _print_palette(palette)
    image_path = render_story(palette)
    print(f"Generated story: {image_path.name}")

    public_url = get_public_image_url(image_path)
    client = InstagramClient()
    media_id = client.publish_story(public_url)
    print(f"Published story: media_id={media_id}")

    if not sample:
        record_published_palette("story", palette)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        run_story_pipeline(sample=args.sample, model=args.model)
        return 0
    except EnvironmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Tip: run with --sample to test locally without an API key.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Story pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
