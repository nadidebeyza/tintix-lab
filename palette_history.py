"""Rolling palette history — 30 unique story/post entries before repeat."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from colors import delta_e_cie76, hex_to_lab
from gemini_client import Palette, palette_fingerprint

Format = Literal["story", "post"]

BASE_DIR = Path(__file__).resolve().parent
HISTORY_SIZE = int(os.getenv("PALETTE_HISTORY_SIZE", "30"))
MIN_COLOR_DISTANCE = float(os.getenv("MIN_COLOR_DISTANCE", "12.0"))
STORY_HISTORY_PATH = BASE_DIR / "story_history.json"
POST_HISTORY_PATH = BASE_DIR / "post_history.json"


def history_path(kind: Format) -> Path:
    return STORY_HISTORY_PATH if kind == "story" else POST_HISTORY_PATH


def _entry_from_palette(palette: Palette) -> dict[str, str]:
    return {
        "theme": palette.theme,
        "fingerprint": palette_fingerprint(palette),
        "bands": ", ".join(f"{band.name} ({band.hex})" for band in palette.bands),
        "published_at": datetime.now(timezone.utc).isoformat(),
    }


def load_history(kind: Format) -> list[dict[str, str]]:
    path = history_path(kind)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload.get("entries", [])
        if isinstance(entries, list):
            return entries[-HISTORY_SIZE:]
    except (OSError, json.JSONDecodeError, TypeError):
        print(f"Warning: {path.name} unreadable — starting with empty history")
    return []


def save_history(kind: Format, entries: list[dict[str, str]]) -> None:
    trimmed = entries[-HISTORY_SIZE:]
    history_path(kind).write_text(
        json.dumps({"entries": trimmed}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _extract_hexes_from_bands(bands_str: str) -> list[str]:
    """Extract hex codes from bands string like 'butter (#feefb8), milk tea (#d8c4b6)'."""
    return re.findall(r"#[0-9a-fA-F]{6}", bands_str)


def _extract_names_from_bands(bands_str: str) -> list[str]:
    """Extract color names from bands string like 'butter (#feefb8), milk tea (#d8c4b6)'."""
    names = re.findall(r"([a-zA-Z][a-zA-Z\s]*?)\s*\(#[0-9a-fA-F]{6}\)", bands_str)
    return [name.strip().lower() for name in names if name.strip()]


def _get_all_history_hexes(history: list[dict[str, str]]) -> list[str]:
    """Collect all hex codes from history entries."""
    hexes: list[str] = []
    for entry in history:
        bands_str = entry.get("bands", "")
        hexes.extend(_extract_hexes_from_bands(bands_str))
    return hexes


def get_recent_color_names(history: list[dict[str, str]]) -> set[str]:
    """Collect all color names from history entries."""
    names: set[str] = set()
    for entry in history:
        bands_str = entry.get("bands", "")
        names.update(_extract_names_from_bands(bands_str))
    return names


def is_color_too_similar(palette: Palette, history: list[dict[str, str]]) -> bool:
    """
    Check if any color in the new palette is perceptually too similar
    to any color in recent history using Delta E (CIE76).
    """
    if not history:
        return False

    history_hexes = _get_all_history_hexes(history)
    if not history_hexes:
        return False

    history_labs = [hex_to_lab(h) for h in history_hexes]

    for band in palette.bands:
        new_lab = hex_to_lab(band.hex)
        for old_lab in history_labs:
            distance = delta_e_cie76(new_lab, old_lab)
            if distance < MIN_COLOR_DISTANCE:
                return True
    return False


def is_duplicate_palette(palette: Palette, history: list[dict[str, str]]) -> bool:
    fingerprint = palette_fingerprint(palette)
    theme = palette.theme.strip().lower()
    for entry in history:
        if entry.get("fingerprint") == fingerprint:
            return True
        if entry.get("theme", "").strip().lower() == theme:
            return True
    if is_color_too_similar(palette, history):
        return True
    return False


def record_published_palette(kind: Format, palette: Palette) -> None:
    history = load_history(kind)
    history.append(_entry_from_palette(palette))
    save_history(kind, history)
    print(
        f"History updated ({kind}): {min(len(history), HISTORY_SIZE)}/{HISTORY_SIZE} — {palette.theme}"
    )


def format_history_for_prompt(kind: Format, history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    label = "story palettes" if kind == "story" else "feed post palettes"
    lines = [
        f"\n\nRecently published — DO NOT REUSE any of these last "
        f"{len(history)} {label}:\n"
    ]
    for entry in history:
        lines.append(f"- {entry.get('theme')} [{entry.get('bands', '')}]\n")
    lines.append("Pick a completely different palette not on this list.\n")

    used_names = get_recent_color_names(history)
    if used_names:
        sorted_names = sorted(used_names)
        lines.append(
            f"\nAvoid these recently used color names: {', '.join(sorted_names)}.\n"
            "Use fresh, creative names that haven't appeared recently."
        )

    return "".join(lines)
