"""30-day unique palette rotation for story and post."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import config
from gemini_client import Palette, palette_fingerprint, palette_from_dict

Format = Literal["story", "post"]


class PalettePoolError(Exception):
    pass


def _pool_path(kind: Format) -> Path:
    return config.POOLS_DIR / f"{kind}.json"


def _default_state() -> dict:
    return {"story": {"index": 0, "cycle": 1}, "post": {"index": 0, "cycle": 1}}


def load_state() -> dict:
    if not config.STATE_FILE.exists():
        return _default_state()
    data = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
    for kind in ("story", "post"):
        if kind not in data:
            data[kind] = {"index": 0, "cycle": 1}
    return data


def save_state(state: dict) -> None:
    config.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_pool(kind: Format) -> list[Palette]:
    path = _pool_path(kind)
    if not path.exists():
        raise PalettePoolError(
            f"Missing palette pool: {path}. Run: python scripts/build_pools.py"
        )

    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("palettes") if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        raise PalettePoolError(f"Invalid pool format in {path}")

    palettes = [palette_from_dict(item) for item in entries]
    if len(palettes) != config.POOL_SIZE:
        raise PalettePoolError(
            f"{kind} pool must contain exactly {config.POOL_SIZE} palettes, got {len(palettes)}"
        )

    fingerprints: set[str] = set()
    for i, palette in enumerate(palettes):
        fp = palette_fingerprint(palette)
        if fp in fingerprints:
            raise PalettePoolError(f"Duplicate palette in {kind} pool at index {i}: {fp}")
        fingerprints.add(fp)

    return palettes


def get_next_palette(kind: Format) -> tuple[Palette, int, int]:
    """Return palette at current index without advancing."""
    pool = load_pool(kind)
    state = load_state()
    index = int(state[kind]["index"])
    cycle = int(state[kind].get("cycle", 1))

    if index < 0 or index >= config.POOL_SIZE:
        raise PalettePoolError(f"Invalid {kind} index {index} in state file")

    palette = pool[index]
    print(f"Using {kind} palette {index + 1}/{config.POOL_SIZE} (cycle {cycle})")
    print(f"Theme: {palette.theme}")
    return palette, index, cycle


def advance_after_publish(kind: Format, published_index: int) -> None:
    """Move to next palette only after a successful publish."""
    state = load_state()
    current = int(state[kind]["index"])
    if current != published_index:
        raise PalettePoolError(
            f"State mismatch for {kind}: expected index {published_index}, found {current}"
        )

    next_index = (current + 1) % config.POOL_SIZE
    state[kind]["index"] = next_index
    if next_index == 0:
        state[kind]["cycle"] = int(state[kind].get("cycle", 1)) + 1
        print(f"{kind} pool completed a full cycle; restarting from palette 1")

    save_state(state)
    print(f"Next {kind} index: {next_index + 1}/{config.POOL_SIZE}")
