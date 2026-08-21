"""Rolling palette history — 30 unique story/post entries before repeat."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from gemini_client import Palette, palette_fingerprint

Format = Literal["story", "post"]

BASE_DIR = Path(__file__).resolve().parent
HISTORY_SIZE = int(os.getenv("PALETTE_HISTORY_SIZE", "30"))
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


def is_duplicate_palette(palette: Palette, history: list[dict[str, str]]) -> bool:
    fingerprint = palette_fingerprint(palette)
    theme = palette.theme.strip().lower()
    for entry in history:
        if entry.get("fingerprint") == fingerprint:
            return True
        if entry.get("theme", "").strip().lower() == theme:
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
    lines.append("Pick a completely different palette not on this list.")
    return "".join(lines)
