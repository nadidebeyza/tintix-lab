#!/usr/bin/env python3
"""Build 30 unique story palettes and 30 unique post palettes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config
from gemini_client import palette_fingerprint, palette_from_dict, palette_to_dict

CAPTION_SUFFIX = "#tintixlab #colorpalette #outfitideas #aesthetic #genzfashion"

STORY_PALETTES = [
    ("Morning Matcha", [("matcha", "#c8ddb5"), ("cream", "#f5f0e6"), ("moss", "#4a5c3f")], "soft matcha mornings for your coziest OOTD 🍵✨"),
    ("Blush Hour", [("blush", "#f2c4c4"), ("petal", "#fde8e8"), ("mocha", "#5c4033")], "blush hour palette for soft-girl fits 🩰"),
    ("Latte Layers", [("latte", "#d4b896"), ("foam", "#faf6f0"), ("espresso", "#3b2f2f")], "layer like a latte — neutral girl era ☕️"),
    ("Cloud Nine", [("cloud", "#e8eef2"), ("mist", "#cfd8dc"), ("slate", "#455a64")], "cloud-core colors for rainy day fits ☁️"),
    ("Cherry Coke", [("cherry", "#d96a6a"), ("vanilla", "#fff5e8"), ("cola", "#3d1f1f")], "cherry coke girl energy — bold but cute 🍒"),
    ("Sage Season", [("sage", "#b7c4a8"), ("linen", "#f0ebe3"), ("olive", "#556b2f")], "sage season is here — earth tone girlies rise 🌿"),
    ("Vanilla Sky", [("vanilla", "#fff8e7"), ("haze", "#e6dccf"), ("cocoa", "#4e342e")], "vanilla sky vibes for clean girl fits 🤍"),
    ("Lilac Dream", [("lilac", "#d8c4e8"), ("mist", "#f3edf7"), ("plum", "#5e3d6b")], "lilac dream palette for ballet-core looks 💜"),
    ("Peach Fuzz", [("peach", "#ffd4b8"), ("cream", "#fff9f2"), ("terracotta", "#b5651d")], "peach fuzz season — warm and glowy 🍑"),
    ("Ocean Mist", [("seafoam", "#b8d8d8"), ("shell", "#f7f3ee"), ("navy", "#1e3a5f")], "ocean mist tones for coastal girl fits 🌊"),
    ("Mocha Mousse", [("mousse", "#c4a484"), ("milk", "#f5ede4"), ("dark roast", "#3c2a21")], "mocha mousse palette — your coffee date uniform ☕️🤎"),
    ("Strawberry Milk", [("strawberry", "#f4b8c4"), ("milk", "#fff5f8"), ("berry", "#8b3a4a")], "strawberry milk girlies this one's for you 🍓"),
    ("Desert Rose", [("rose", "#d4a59a"), ("sand", "#f2e8dc"), ("clay", "#8b5e3c")], "desert rose tones for golden hour outfits 🌵"),
    ("Mint Condition", [("mint", "#b8e0d2"), ("ice", "#f0faf7"), ("pine", "#2f4f4f")], "mint condition palette — fresh and effortless 🌱"),
    ("Honey Glow", [("honey", "#e8c872"), ("butter", "#fff8dc"), ("amber", "#8b6914")], "honey glow colors for sun-kissed fits 🍯"),
    ("Dusty Blue", [("dust", "#a8b8c8"), ("porcelain", "#f4f6f8"), ("ink", "#2c3e50")], "dusty blue mood for quiet luxury fits 💙"),
    ("Coral Sunset", [("coral", "#f08080"), ("peach", "#ffe4c4"), ("wine", "#722f37")], "coral sunset palette for summer night fits 🌅"),
    ("Pistachio Cream", [("pistachio", "#c5d86d"), ("cream", "#faf8f3"), ("forest", "#3d5c3a")], "pistachio cream combo — Pinterest girl approved 🥜"),
    ("Rose Quartz", [("quartz", "#e8b4b8"), ("pearl", "#fdf6f0"), ("wine", "#6b3a3a")], "rose quartz energy for soft romantic fits 💎"),
    ("Butter Yellow", [("butter", "#feefb8"), ("cream", "#fffef5"), ("mustard", "#c4a035")], "butter yellow era — main character sunshine ☀️"),
    ("Milk Tea Trio", [("milk tea", "#d8c4b6"), ("oat", "#f5efe8"), ("boba", "#432f2e")], "milk tea palette for your everyday aesthetic 🧋"),
    ("Lavender Haze", [("lavender", "#c8b6e2"), ("fog", "#ede7f6"), ("violet", "#4a3f6b")], "lavender haze colors for dreamy fits 💫"),
    ("Caramel Swirl", [("caramel", "#c68642"), ("vanilla", "#fff8f0"), ("espresso", "#3e2723")], "caramel swirl palette — sweet but grounded 🍮"),
    ("Sea Salt", [("salt", "#e8ecef"), ("foam", "#f8f9fa"), ("charcoal", "#37474f")], "sea salt neutrals for minimal girl fits 🧂"),
    ("Apricot Jam", [("apricot", "#f5b895"), ("cream", "#fff5eb"), ("rust", "#a0522d")], "apricot jam tones for warm autumn fits 🍑"),
    ("Frozen Berry", [("berry", "#9b6b8e"), ("frost", "#f0e6f0"), ("midnight", "#2d1b3d")], "frozen berry palette for cozy winter fits ❄️"),
    ("Golden Hour", [("gold", "#e8c547"), ("champagne", "#f7f0d4"), ("bronze", "#8b6914")], "golden hour colors — glow up your feed ✨"),
    ("Thrift Find", [("mustard", "#d4a843"), ("denim", "#6b7b8c"), ("corduroy", "#5c4033")], "thrift find palette for vintage girl fits 🛍️"),
    ("Coquette Core", [("ribbon", "#f4c2c2"), ("lace", "#fff0f5"), ("chocolate", "#4a2c2a")], "coquette core colors — bows and blush forever 🎀"),
    ("Matcha Latte", [("matcha", "#a8c686"), ("steamed", "#f0f4ec"), ("roast", "#3e4a32")], "matcha latte palette to save for later 🍵"),
]

POST_PALETTES = [
    ("Autumn Pastels", [("butter", "#feefb8"), ("milk tea", "#d8c4b6"), ("chocopie", "#432f2e")], "save this for your next coffee date outfit ☕️✨"),
    ("Soft Academia", [("parchment", "#f5f0e1"), ("taupe", "#b8a898"), ("ink", "#2c2416")], "soft academia palette for library girl fits 📚"),
    ("City Sunset", [("peach", "#ffb088"), ("dusk", "#e8a0a0"), ("night", "#2d1f3d")], "city sunset colors for evening stroll fits 🌆"),
    ("Vintage Denim", [("denim", "#6b8cae"), ("wash", "#c5d5e8"), ("indigo", "#1e3a5f")], "vintage denim palette — classic never dies 👖"),
    ("Cottage Core", [("meadow", "#a8c686"), ("cream", "#faf6f0"), ("soil", "#5c4033")], "cottage core colors for picnic day fits 🧺"),
    ("Y2K Candy", [("bubblegum", "#ff9ecd"), ("lemon", "#fff59d"), ("grape", "#7b5ea7")], "y2k candy palette — throwback but make it chic 💿"),
    ("Clean Girl", [("linen", "#f5f0eb"), ("sand", "#d4c4b0"), ("espresso", "#3c2a21")], "clean girl neutrals for effortless fits 🤍"),
    ("Dark Cherry", [("cherry", "#8b2942"), ("blush", "#f2d4d4"), ("noir", "#1a0a0f")], "dark cherry palette for date night fits 🍒"),
    ("Arctic Frost", [("ice", "#d4e8f0"), ("snow", "#f8fbfd"), ("steel", "#4a6670")], "arctic frost tones for winter layering ❄️"),
    ("Tropical Punch", [("mango", "#ffb347"), ("aqua", "#7fcdcd"), ("coral", "#ff6f61")], "tropical punch palette for vacation fits 🌴"),
    ("Old Money", [("ivory", "#fffff0"), ("camel", "#c19a6b"), ("forest", "#2d4a3e")], "old money palette — quiet luxury girl era 💅"),
    ("Grunge Rose", [("rose", "#b56576"), ("smoke", "#6c757d"), ("black", "#1a1a1a")], "grunge rose colors for edgy soft fits 🥀"),
    ("Sunset Drive", [("tangerine", "#ff9966"), ("lavender", "#c8a2c8"), ("twilight", "#4a3f6b")], "sunset drive palette for golden hour fits 🚗"),
    ("Earthy Tones", [("clay", "#b87333"), ("sage", "#9caf88"), ("umber", "#4a3728")], "earthy tones for nature girl outfits 🍂"),
    ("Bubble Bath", [("soap", "#e8f4f8"), ("pink", "#f8d7da"), ("lavender", "#d8c4e8")], "bubble bath palette — self care aesthetic 🛁"),
    ("Retro Sport", [("cream", "#f5f5dc"), ("red", "#c41e3a"), ("navy", "#1e3a5f")], "retro sport colors for athleisure fits 🎾"),
    ("Moonlit Garden", [("moon", "#e8e4f0"), ("petal", "#d4a5a5"), ("midnight", "#2d1b3d")], "moonlit garden palette for romantic fits 🌙"),
    ("Citrus Fresh", [("lemon", "#fff44f"), ("lime", "#c5e384"), ("leaf", "#4a7c59")], "citrus fresh colors for bright summer fits 🍋"),
    ("Warm Minimal", [("oat", "#e8dcc8"), ("stone", "#b8a898"), ("charcoal", "#36454f")], "warm minimal palette for capsule wardrobe fits 🧥"),
    ("Berry Smoothie", [("raspberry", "#c72c48"), ("yogurt", "#fff5f0"), ("acai", "#4a1942")], "berry smoothie palette — gym to brunch fits 🫐"),
    ("Sakura Bloom", [("sakura", "#ffb7c5"), ("blossom", "#ffe4e9"), ("branch", "#5c4033")], "sakura bloom colors for spring fits 🌸"),
    ("Coffee Shop", [("americano", "#3c2415"), ("latte", "#d4b896"), ("foam", "#faf6f0")], "coffee shop palette — your daily uniform ☕️"),
    ("Neon Nights", [("neon", "#39ff14"), ("electric", "#7df9ff"), ("void", "#0d0221")], "neon nights palette for bold street fits 🌃"),
    ("Prairie Warmth", [("wheat", "#f5deb3"), ("rust", "#b7410e"), ("prairie", "#8b7355")], "prairie warmth colors for fall layering 🌾"),
    ("Ice Cream Shop", [("vanilla", "#f3e5ab"), ("mint chip", "#98d8c8"), ("chocolate", "#5c4033")], "ice cream shop palette — sweet summer fits 🍦"),
    ("Studio Beige", [("beige", "#f5f5dc"), ("greige", "#b8a898"), ("espresso", "#3e2723")], "studio beige neutrals for Pinterest board fits 📌"),
    ("Rainy Day", [("rain", "#9eb7c8"), ("cloud", "#e8ecef"), ("storm", "#37474f")], "rainy day palette for cozy indoor fits 🌧️"),
    ("Pistachio Coquette", [("pistachio", "#c5d86d"), ("ballet", "#f4c2c2"), ("cacao", "#4a2c2a")], "pistachio coquette — soft girl energy 🩰🍵"),
    ("Desert Bloom", [("bloom", "#e8a598"), ("sand", "#f2e8dc"), ("cactus", "#6b8e23")], "desert bloom colors for warm weather fits 🌵"),
    ("Midnight Snack", [("midnight", "#191970"), ("cookie", "#d4a574"), ("cream", "#fff8dc")], "midnight snack palette for late night fits 🌙🍪"),
]


def _build_entries(rows: list) -> list[dict]:
    palettes = []
    for theme, bands, hook in rows:
        caption = f"{hook} {CAPTION_SUFFIX}"
        palettes.append(
            {
                "theme": theme,
                "bands": [{"name": name, "hex": hex_code} for name, hex_code in bands],
                "caption": caption,
            }
        )
    return palettes


def _validate(kind: str, entries: list[dict]) -> None:
    if len(entries) != config.POOL_SIZE:
        raise ValueError(f"{kind} pool must have {config.POOL_SIZE} entries, got {len(entries)}")

    seen: set[str] = set()
    for i, entry in enumerate(entries):
        fp = palette_fingerprint(palette_from_dict(entry))
        if fp in seen:
            raise ValueError(f"Duplicate {kind} palette at index {i}: {fp}")
        seen.add(fp)


def write_pool(kind: str, entries: list[dict]) -> Path:
    _validate(kind, entries)
    config.POOLS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.POOLS_DIR / f"{kind}.json"
    payload = {"version": 1, "palettes": entries}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    story_entries = _build_entries(STORY_PALETTES)
    post_entries = _build_entries(POST_PALETTES)
    story_path = write_pool("story", story_entries)
    post_path = write_pool("post", post_entries)
    print(f"Wrote {story_path} ({len(story_entries)} palettes)")
    print(f"Wrote {post_path} ({len(post_entries)} palettes)")


if __name__ == "__main__":
    main()
