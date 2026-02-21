# weather_icons.py - Weather icon spritesheet loader for TFT display
# Loads weather_icons.bmp (horizontal strip, 13 tiles @ 90x90)
# Maps Home Assistant met.no condition strings to tile indices.

import displayio

TILE_SIZE = 90
_sheet = None
_palette = None

# HA met.no condition → tile index in spritesheet
CONDITION_MAP = {
    "sunny":           0,
    "clear-night":     1,
    "partlycloudy":    2,
    "cloudy":          3,
    "fog":             4,
    "rainy":           5,
    "pouring":         6,
    "snowy":           7,
    "lightning":       8,
    "lightning-rainy": 9,
    "windy":          10,
    "hail":           11,
    "unknown":        12,
}

# Fallback aliases for edge cases
_ALIASES = {
    "clear": "sunny",
    "sunny-night": "clear-night",
    "exceptional": "unknown",
}

def load():
    """Load the spritesheet from flash. Call once at boot."""
    global _sheet, _palette
    _sheet = displayio.OnDiskBitmap("/weather_icons.bmp")
    _palette = _sheet.pixel_shader
    print("[weather_icons] Loaded spritesheet")

def tile(condition: str) -> displayio.TileGrid:
    """Return a TileGrid for the given HA weather condition string."""
    if _sheet is None:
        load()

    cond = condition.lower().replace(" ", "").replace("_", "-")
    idx = CONDITION_MAP.get(cond)
    if idx is None:
        idx = CONDITION_MAP.get(_ALIASES.get(cond, ""), 12)

    return displayio.TileGrid(
        _sheet,
        pixel_shader=_palette,
        width=1,
        height=1,
        tile_width=TILE_SIZE,
        tile_height=TILE_SIZE,
        default_tile=idx,
    )