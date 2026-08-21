"""Gemini API integration for palette generation."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Literal

GEMINI_PROMPT_BASE = """
You are a Gen-Z fashion color theorist and stylist for the Instagram page @tintix.lab.
Your task is to create a trendy, aesthetic 3-color palette that girls aged 16-25 can use for outfit styling, makeup, or room aesthetics.

Return ONLY a valid JSON object with no markdown backticks:
{
  "theme": "Aesthetic Theme Name",
  "bands": [
    {
      "name": "butter",
      "hex": "#HEXCODE1"
    },
    {
      "name": "milk tea",
      "hex": "#HEXCODE2"
    },
    {
      "name": "chocopie",
      "hex": "#HEXCODE3"
    }
  ],
  "caption": "An engaging, friendly Instagram caption with aesthetic emojis and relevant hashtags including #tintixlab."
}

Rules:
1. 'name' must be short, all-lowercase (1-2 words max, e.g., 'powder', 'butter', 'chocopie', 'lacté', 'matcha', 'espresso').
2. Color hexes must harmonize beautifully (e.g., 2 soft pastel/muted tones + 1 rich grounding tone).
3. NEVER repeat any palette listed in the "Recently published — DO NOT REUSE" section.
"""

Format = Literal["story", "post"]
DUPLICATE_RETRIES = int(os.getenv("DUPLICATE_PALETTE_RETRIES", "5"))

# Tried in order; each model has its own free-tier quota bucket.
MODEL_FALLBACKS = (
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.6-flash",
)


@dataclass
class Band:
    name: str
    hex: str


@dataclass
class Palette:
    theme: str
    bands: list[Band]
    caption: str


def _extract_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _normalize_palette(data: dict[str, Any]) -> Palette:
    theme = data.get("theme") or data.get("palette_name") or "Untitled Palette"
    bands_raw = data.get("bands") or []
    if len(bands_raw) != 3:
        raise ValueError("Gemini response must contain exactly 3 color bands.")

    bands = [
        Band(name=str(item["name"]).lower(), hex=str(item["hex"]))
        for item in bands_raw
    ]
    caption = str(data.get("caption", "")).strip()
    return Palette(theme=theme, bands=bands, caption=caption)


def _retry_delay_seconds(error: Exception) -> int | None:
    match = re.search(r"retry in (\d+(?:\.\d+)?)s", str(error), re.IGNORECASE)
    if match:
        return max(1, int(float(match.group(1))))
    return None


def _is_retryable(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        token in message
        for token in (
            "429",
            "503",
            "quota",
            "rate limit",
            "resource exhausted",
            "unavailable",
            "high demand",
            "404",
            "not_found",
            "no longer available",
        )
    )


def _call_model(client, model: str, prompt: str) -> Palette:
    response = client.models.generate_content(model=model, contents=prompt)
    data = _extract_json(response.text)
    return _normalize_palette(data)


def build_gemini_prompt(
    kind: Format,
    history: list[dict[str, str]],
    *,
    duplicate_retry: bool = False,
) -> str:
    from palette_history import format_history_for_prompt

    prompt = GEMINI_PROMPT_BASE + format_history_for_prompt(kind, history)
    if duplicate_retry:
        prompt += (
            "\nYour previous answer duplicated a banned palette. "
            "Generate something entirely new — different theme and different hex codes."
        )
    return prompt


def _generate_once(client, models: list[str], prompt: str) -> Palette:
    errors: list[str] = []
    for candidate in models:
        try:
            palette = _call_model(client, candidate, prompt)
            if candidate != models[0]:
                print(f"Note: used fallback model '{candidate}' (primary quota unavailable).")
            return palette
        except Exception as exc:
            if _is_retryable(exc):
                delay = _retry_delay_seconds(exc)
                if delay and delay <= 60:
                    print(f"Rate limited on {candidate}, retrying in {delay}s...")
                    time.sleep(delay)
                    try:
                        return _call_model(client, candidate, prompt)
                    except Exception as retry_exc:
                        errors.append(f"{candidate}: {retry_exc}")
                        continue
                errors.append(f"{candidate}: {exc}")
                continue
            raise
    raise RuntimeError(
        "All Gemini models failed (quota or rate limit). "
        f"Details: {' | '.join(errors)}"
    )


def generate_palette(
    kind: Format = "post",
    api_key: str | None = None,
    model: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> Palette:
    """Call Gemini and return a palette not in recent history."""
    from palette_history import HISTORY_SIZE, is_duplicate_palette, load_history

    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to your environment or .env file."
        )

    from google import genai

    recent = history if history is not None else load_history(kind)
    if recent:
        print(f"Avoiding {len(recent)} recent {kind} palettes from history (max {HISTORY_SIZE})")

    client = genai.Client(api_key=key)
    preferred = model or os.getenv("GEMINI_MODEL")
    models = [preferred] if preferred else list(MODEL_FALLBACKS)
    for fallback in MODEL_FALLBACKS:
        if fallback not in models:
            models.append(fallback)

    for duplicate_attempt in range(1, DUPLICATE_RETRIES + 1):
        prompt = build_gemini_prompt(
            kind,
            recent,
            duplicate_retry=duplicate_attempt > 1,
        )
        palette = _generate_once(client, models, prompt)
        if not is_duplicate_palette(palette, recent):
            return palette
        print(
            f"Duplicate blocked: {palette.theme} — regenerating "
            f"({duplicate_attempt}/{DUPLICATE_RETRIES})"
        )

    raise RuntimeError(
        f"Could not generate a unique {kind} palette after {DUPLICATE_RETRIES} attempts. "
        "Review story_history.json / post_history.json or increase DUPLICATE_PALETTE_RETRIES."
    )


def palette_fingerprint(palette: Palette) -> str:
    """Stable identity for deduplication within a pool."""
    from colors import normalize_hex

    hexes = "|".join(sorted(normalize_hex(b.hex).lower() for b in palette.bands))
    names = "|".join(b.name.lower() for b in palette.bands)
    return f"{palette.theme.strip().lower()}::{names}::{hexes}"


def palette_to_dict(palette: Palette) -> dict[str, Any]:
    return {
        "theme": palette.theme,
        "bands": [{"name": b.name, "hex": b.hex} for b in palette.bands],
        "caption": palette.caption,
    }


def palette_from_dict(data: dict[str, Any]) -> Palette:
    return _normalize_palette(data)


def sample_palette() -> Palette:
    """Offline fallback for local design testing."""
    return Palette(
        theme="Autumn Pastels",
        bands=[
            Band(name="butter", hex="#feefb8"),
            Band(name="milk tea", hex="#d8c4b6"),
            Band(name="chocopie", hex="#432f2e"),
        ],
        caption=(
            "Save this palette for your next coffee date outfit ☕️✨ "
            "#tintixlab #outfitideas #colorpalette #genzfashion"
        ),
    )
