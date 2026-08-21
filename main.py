#!/usr/bin/env python3
"""
@tintix.lab — Instagram Post automation pipeline.

Generates palette via Gemini, renders 1080×1080 card, hosts publicly,
and publishes to Instagram. Tracks last 30 post palettes in post_history.json.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

import canvas
import config
from gemini_client import Palette, generate_palette, sample_palette
from image_host import get_public_image_url
from instagram_client import InstagramClient
from instagram_setup import verify_instagram_setup
from palette_history import record_published_palette

OUTPUT_POST = config.BASE_DIR / "final_post.png"


def render_post(palette: Palette) -> Path:
    image = canvas.render_palette_card(palette, config.POST_SIZE)
    return canvas.save_image(image, OUTPUT_POST)


def _print_palette(palette: Palette) -> None:
    print(f"Theme: {palette.theme}")
    for i, band in enumerate(palette.bands, 1):
        print(f"  Band {i}: {band.name} — {band.hex}")
    print(f"\nCaption:\n{palette.caption}\n")


def run_post_pipeline(*, sample: bool = False, model: str | None = None) -> None:
    verify_instagram_setup()

    if sample:
        palette = sample_palette()
    else:
        palette = generate_palette("post", model=model)

    _print_palette(palette)
    image_path = render_post(palette)
    print(f"Generated post: {image_path.name}")

    public_url = get_public_image_url(image_path)
    client = InstagramClient()
    media_id = client.publish_post(public_url, palette.caption)
    print(f"Published post: media_id={media_id}")

    if not sample:
        record_published_palette("post", palette)


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
        run_post_pipeline(sample=args.sample, model=args.model)
        return 0
    except EnvironmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Tip: run with --sample to test locally without an API key.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Post pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
