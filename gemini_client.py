"""Gemini API integration for palette generation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

GEMINI_PROMPT = """
You are a Gen-Z fashion color theorist and stylist for the Instagram page @tintix.lab.
Your task is to create a trendy, aesthetic 3-color palette that girls aged 16-25 can use for outfit styling, makeup, or room aesthetics.

Return ONLY a valid JSON object with no markdown backticks:
{
  "theme": "Aesthetic Theme Name",
  "bands": [
    {
      "name": "SHORT_CATCHY_NAME_1",
      "hex": "#HEXCODE1"
    },
    {
      "name": "SHORT_CATCHY_NAME_2",
      "hex": "#HEXCODE2"
    },
    {
      "name": "SHORT_CATCHY_NAME_3",
      "hex": "#HEXCODE3"
    }
  ],
  "caption": "An engaging, friendly Instagram caption with aesthetic emojis and relevant hashtags including #tintixlab."
}

Rules:
1. 'name' must be short (1-2 words max, e.g., 'POWDER', 'BUTTER', 'CHOCOPIE', 'LACTÉ', 'MATCHA', 'ESPRESSO').
2. Color hexes must harmonize beautifully (e.g., 2 soft pastel/muted tones + 1 rich grounding tone).
"""


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
        Band(name=str(item["name"]).upper(), hex=str(item["hex"]))
        for item in bands_raw
    ]
    caption = str(data.get("caption", "")).strip()
    return Palette(theme=theme, bands=bands, caption=caption)


def generate_palette(api_key: str | None = None, model: str = "gemini-3.6-flash") -> Palette:
    """Call Gemini and return a validated palette."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to your environment or .env file."
        )

    import google.generativeai as genai

    genai.configure(api_key=key)
    client = genai.GenerativeModel(model)
    response = client.generate_content(GEMINI_PROMPT)
    data = _extract_json(response.text)
    return _normalize_palette(data)


def sample_palette() -> Palette:
    """Offline fallback for local design testing."""
    return Palette(
        theme="Autumn Pastels",
        bands=[
            Band(name="BUTTER", hex="#feefb8"),
            Band(name="MILK TEA", hex="#d8c4b6"),
            Band(name="CHOCOPIE", hex="#432f2e"),
        ],
        caption=(
            "Save this palette for your next coffee date outfit ☕️✨ "
            "#tintixlab #outfitideas #colorpalette #genzfashion"
        ),
    )
