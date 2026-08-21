"""Brand and layout constants for @tintix.lab."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Instagram canvas sizes
STORY_SIZE = (1080, 1920)
POST_SIZE = (1080, 1080)

# Typography scale (relative to canvas height)
TITLE_FONT_RATIO = 0.068
HEX_FONT_RATIO = 0.022
NAME_HEX_GAP_RATIO = 0.95

# Padding from edges
EDGE_PADDING_RATIO = 0.045

OUTPUT_DIR = "output"
