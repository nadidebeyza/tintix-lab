#!/usr/bin/env python3
"""@tintix.lab — run story or post generation separately."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate @tintix.lab Instagram palette cards via Gemini + Pillow.",
    )
    parser.add_argument(
        "format",
        choices=("story", "post"),
        help="Publish a story or a post (run separately).",
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
    args = build_parser().parse_args(argv)
    passthrough = []
    if args.sample:
        passthrough.append("--sample")
    if args.model:
        passthrough.extend(["--model", args.model])

    if args.format == "story":
        from story import main as story_main

        return story_main(passthrough)
    from post import main as post_main

    return post_main(passthrough)


if __name__ == "__main__":
    raise SystemExit(main())
