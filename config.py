"""Brand and layout constants for @tintix.lab."""

from pathlib import Path

BRAND_HANDLE = "@tintix.lab"

# Instagram canvas sizes
STORY_SIZE = (1080, 1920)
POST_SIZE = (1080, 1080)

# Typography scale (relative to canvas height)
HEADER_FONT_RATIO = 0.026
BRAND_HANDLE_TRACKING_RATIO = 0.035
TITLE_FONT_RATIO = 0.068
HEX_FONT_RATIO = 0.022
NAME_HEX_GAP_RATIO = 0.95

# Padding from edges
EDGE_PADDING_RATIO = 0.045
BAND_HEADER_OFFSET_RATIO = 0.035

OUTPUT_DIR = "output"

# Palette rotation (30 unique story + 30 unique post before repeat)
POOL_SIZE = 30
DATA_DIR = Path(__file__).parent / "data"
POOLS_DIR = DATA_DIR / "pools"
STATE_FILE = DATA_DIR / "state.json"
