#!/usr/bin/env python3
"""@tintix.lab — Instagram Story & Post palette generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

import config
from gemini_client import generate_palette, sample_palette
from instagram_client import publish_to_instagram
from post import generate_post
from story import generate_story


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate @tintix.lab Instagram palette cards via Gemini + Pillow.",
    )
    parser.add_argument(
        "--format",
        choices=("story", "post", "both"),
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--output-dir",
        default=config.OUTPUT_DIR,
        help=f"Directory for PNG output (default: {config.OUTPUT_DIR})",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use built-in sample palette (no Gemini API call)",
    )
    parser.add_argument(
        "--model",
        default="gemini-3.6-flash",
        help="Gemini model name (default: gemini-3.6-flash)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish generated images to Instagram (requires Graph API credentials)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)

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

    story_path: Path | None = None
    post_path: Path | None = None

    if args.format in ("story", "both"):
        story_path = generate_story(palette, output_dir)
        print(f"Saved: {story_path.resolve()}")
    if args.format in ("post", "both"):
        post_path = generate_post(palette, output_dir)
        print(f"Saved: {post_path.resolve()}")

    caption_path = output_dir / "caption.txt"
    caption_path.write_text(palette.caption, encoding="utf-8")
    print(f"Saved: {caption_path.resolve()}")

    if args.publish:
        try:
            results = publish_to_instagram(
                post_path=post_path,
                story_path=story_path,
                caption=palette.caption,
                publish_post=post_path is not None,
                publish_story=story_path is not None,
            )
            for kind, media_id in results.items():
                print(f"Published {kind}: media_id={media_id}")
        except Exception as exc:
            print(f"Instagram publish failed: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
