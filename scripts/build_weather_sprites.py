#!/usr/bin/env python3
"""
Build weather icon spritesheet for SmartToolbox ESP32-S3 TFT display.
Renders Tabler Icons SVGs at 90x90 pixels, cyan (#00d4ff) on black.
Output: indexed-color BMP suitable for CircuitPython OnDiskBitmap + TileGrid.

Usage:
    pip install cairosvg Pillow
    python build_weather_sprites.py

Output: firmware/weather_icons.bmp
"""

import io, os
from PIL import Image
import cairosvg

TILE_SIZE = 90
ICON_COLOR = (0x00, 0xD4, 0xFF)
BG_COLOR = (0x00, 0x00, 0x00)
STROKE_WIDTH = "1.5"

CONDITIONS = [
    ("sunny",           "sun"),
    ("clear-night",     "moon"),
    ("partlycloudy",    "cloud-sun"),
    ("cloudy",          "cloud"),
    ("fog",             "fog"),
    ("rainy",           "cloud-rain"),    ("pouring",         "cloud-rain-heavy"),
    ("snowy",           "snowflake"),
    ("lightning",       "bolt"),
    ("lightning-rainy", "cloud-bolt"),
    ("windy",           "wind"),
    ("hail",            "hail"),
    ("unknown",         "question"),
]

SVG_PATHS = {
    "sun": [
        '<path d="M8 12a4 4 0 1 0 8 0a4 4 0 1 0 -8 0"/>',
        '<path d="M3 12h1m8 -9v1m8 8h1m-9 8v1m-6.4 -15.4l.7 .7m12.1 -.7l-.7 .7m0 11.4l.7 .7m-12.1 -.7l-.7 .7"/>',
    ],
    "moon": [
        '<path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454l0 .008"/>',
    ],
    "cloud-sun": [
        '<path d="M6.657 18c-2.572 0 -4.657 -2.007 -4.657 -4.483c0 -2.475 2.085 -4.482 4.657 -4.482c.393 -1.762 1.794 -3.2 3.675 -3.773c1.88 -.572 3.956 -.193 5.444 1c1.488 1.19 2.162 3.007 1.77 4.769h.99c1.913 0 3.464 1.56 3.464 3.486c0 1.927 -1.551 3.487 -3.465 3.487h-11.878"/>',
        '<circle cx="19" cy="5" r="2.5"/>',
        '<path d="M19 1v1m0 6v1m-3 -5.5h1m4 0h1m-1.5 -2.5l-.5 .5m-3 3l-.5 .5m4 0l.5 .5m-3 -3l.5 -.5"/>',
    ],
    "cloud": [
        '<path d="M6.657 18c-2.572 0 -4.657 -2.007 -4.657 -4.483c0 -2.475 2.085 -4.482 4.657 -4.482c.393 -1.762 1.794 -3.2 3.675 -3.773c1.88 -.572 3.956 -.193 5.444 1c1.488 1.19 2.162 3.007 1.77 4.769h.99c1.913 0 3.464 1.56 3.464 3.486c0 1.927 -1.551 3.487 -3.465 3.487h-11.878"/>',
    ],
    "fog": [
        '<path d="M7 18a4.6 4.4 0 0 1 0 -9a5 4.5 0 0 1 11 2h1a3.5 3.5 0 0 1 0 7"/>',
        '<path d="M5 20h14"/>',
        '<path d="M3 22h18"/>',
    ],    "cloud-rain": [
        '<path d="M7 18a4.6 4.4 0 0 1 0 -9a5 4.5 0 0 1 11 2h1a3.5 3.5 0 0 1 0 7"/>',
        '<path d="M11 13v2m0 3v2m4 -5v2m0 3v2"/>',
    ],
    "cloud-rain-heavy": [
        '<path d="M7 18a4.6 4.4 0 0 1 0 -9a5 4.5 0 0 1 11 2h1a3.5 3.5 0 0 1 0 7"/>',
        '<path d="M8 13v2m0 3v2m4 -5v2m0 3v2m4 -5v2m0 3v2"/>',
    ],
    "snowflake": [
        '<path d="M10 4l2 1l2 -1"/>',
        '<path d="M12 2v6.5l3 1.72"/>',
        '<path d="M17.928 6.268l.134 2.232l1.866 1.232"/>',
        '<path d="M20.66 7l-5.629 3.25l.01 3.458"/>',
        '<path d="M19.928 14.268l-1.866 1.232l-.134 2.232"/>',
        '<path d="M20.66 17l-5.629 -3.25l-2.99 1.738"/>',
        '<path d="M14 20l-2 -1l-2 1"/>',
        '<path d="M12 22v-6.5l-3 -1.72"/>',
        '<path d="M6.072 17.732l-.134 -2.232l-1.866 -1.232"/>',
        '<path d="M3.34 17l5.629 -3.25l-.01 -3.458"/>',
        '<path d="M4.072 9.732l1.866 -1.232l.134 -2.232"/>',
        '<path d="M3.34 7l5.629 3.25l2.99 -1.738"/>',
    ],
    "bolt": [
        '<path d="M13 3l0 7l6 0l-8 11l0 -7l-6 0l8 -11"/>',
    ],
    "cloud-bolt": [
        '<path d="M7 18a4.6 4.4 0 0 1 0 -9a5 4.5 0 0 1 11 2h1a3.5 3.5 0 0 1 0 7"/>',
        '<path d="M13 14l-2 4h4l-2 4"/>',
    ],    "wind": [
        '<path d="M5 8h8.5a2.5 2.5 0 1 0 -2.34 -3.24"/>',
        '<path d="M3 12h15.5a2.5 2.5 0 1 1 -2.34 3.24"/>',
        '<path d="M4 16h5.5a2.5 2.5 0 1 1 -2.34 3.24"/>',
    ],
    "hail": [
        '<path d="M7 18a4.6 4.4 0 0 1 0 -9a5 4.5 0 0 1 11 2h1a3.5 3.5 0 0 1 0 7"/>',
        '<circle cx="10" cy="21" r="1" fill="currentColor"/>',
        '<circle cx="14" cy="19" r="1" fill="currentColor"/>',
        '<circle cx="17" cy="21" r="1" fill="currentColor"/>',
    ],
    "question": [
        '<path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"/>',
        '<path d="M12 17l0 .01"/>',
        '<path d="M12 13.5a1.5 1.5 0 0 1 1 -1.5a2.6 2.6 0 1 0 -3 -4"/>',
    ],
}


def make_svg(icon_name):
    paths = SVG_PATHS[icon_name]
    inner = "\n  ".join(paths)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
  viewBox="0 0 24 24" fill="none" stroke="#00d4ff"
  stroke-width="{STROKE_WIDTH}" stroke-linecap="round" stroke-linejoin="round">
  <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
  {inner}
</svg>'''

def svg_to_image(svg_str, size):
    png_data = cairosvg.svg2png(
        bytestring=svg_str.encode("utf-8"),
        output_width=size, output_height=size,
        background_color="#000000",
    )
    img = Image.open(io.BytesIO(png_data)).convert("RGBA")
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    bg.paste(img, (0, 0), img)
    return bg.convert("RGB")


def threshold_to_indexed(img):
    w, h = img.size
    indexed = Image.new("P", (w, h))
    palette = [0] * 768
    palette[0], palette[1], palette[2] = BG_COLOR
    palette[3], palette[4], palette[5] = ICON_COLOR
    indexed.putpalette(palette)
    src = img.load()
    dst = indexed.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            dst[x, y] = 1 if r + g + b > 40 else 0
    return indexed

def build_spritesheet(tiles, tile_size):
    n = len(tiles)
    sheet = Image.new("P", (tile_size * n, tile_size))
    sheet.putpalette(tiles[0].getpalette())
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (i * tile_size, 0))
    return sheet


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    out_path = os.path.join(project_dir, "firmware", "weather_icons.bmp")

    print(f"Building weather spritesheet: {len(CONDITIONS)} tiles @ {TILE_SIZE}x{TILE_SIZE}")
    tiles = []
    for condition, icon_name in CONDITIONS:
        print(f"  [{len(tiles):2d}] {condition:20s} -> {icon_name}")
        svg_str = make_svg(icon_name)
        rgb_img = svg_to_image(svg_str, TILE_SIZE)
        indexed_img = threshold_to_indexed(rgb_img)
        tiles.append(indexed_img)

    sheet = build_spritesheet(tiles, TILE_SIZE)
    sheet.save(out_path, format="BMP")
    w, h = sheet.size
    print(f"\nSpritesheet: {w}x{h} -> {out_path}")
    print(f"Tiles: {len(tiles)}, tile_size: {TILE_SIZE}x{TILE_SIZE}")


if __name__ == "__main__":
    main()