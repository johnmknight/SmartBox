# modes/interrupts/red_alert.py — Star Trek II "Wrath of Khan" style
# Static chevrons + text, animated scan line brightness sweep.
# Animation uses palette-only updates (zero redraw, no flicker).

import displayio, terminalio, time
from adafruit_display_text import label
import display, settings

_group = None
_top_pals = []    # palette refs for top scan bars
_bot_pals = []    # palette refs for bottom scan bars
_built = False

def reset():
    global _group, _built
    _group = None
    _built = False

def _line(bm, x1, y1, x2, y2, color_idx, thick=2):
    """Draw a line into a bitmap using DDA."""
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy)) or 1
    xi = dx / steps
    yi = dy / steps
    x, y = float(x1), float(y1)
    for _ in range(steps + 1):
        px, py = int(x), int(y)
        for t in range(thick):
            if 0 <= px + t < bm.width and 0 <= py < bm.height:
                bm[px + t, py] = color_idx
        x += xi
        y += yi
def _build():
    global _group, _top_pals, _bot_pals, _built
    _top_pals = []
    _bot_pals = []
    g = displayio.Group()

    # Background + chevron lines
    bg = displayio.Bitmap(240, 135, 2)
    bp = displayio.Palette(2)
    bp[0] = 0x000000
    bp[1] = 0xCC0000

    TX_L = 39; TX_R = 201; MID_Y = 67; TOP_Y = 20; BOT_Y = 115
    _line(bg, TX_L, TOP_Y, 0, MID_Y, 1, thick=10)
    _line(bg, 0, MID_Y, TX_L, BOT_Y, 1, thick=10)
    RX = 226
    _line(bg, TX_R, TOP_Y, RX, MID_Y, 1, thick=10)
    _line(bg, RX, MID_Y, TX_R, BOT_Y, 1, thick=10)
    g.append(displayio.TileGrid(bg, pixel_shader=bp))

    # Scan line bars — fixed count, perfectly mirrored
    BAR_W, BAR_H, GAP = 100, 3, 3
    NUM_BARS = 5
    bx = (240 - BAR_W) // 2
    STEP = BAR_H + GAP  # 6px per bar slot

    # Top bars: y = 20, 26, 32, 38, 44 (index 0=top, 4=nearest center)
    for i in range(NUM_BARS):
        y = 20 + i * STEP
        bm = displayio.Bitmap(BAR_W, BAR_H, 1)
        pal = displayio.Palette(1); pal[0] = 0x440000
        g.append(displayio.TileGrid(bm, pixel_shader=pal, x=bx, y=y))
        _top_pals.append(pal)

    # Bottom bars: mirrored from bottom edge (index 0=bottom, 4=nearest center)
    for i in range(NUM_BARS):
        y = (135 - 20 - BAR_H) - i * STEP  # 112, 106, 100, 94, 88
        bm = displayio.Bitmap(BAR_W, BAR_H, 1)
        pal = displayio.Palette(1); pal[0] = 0x440000
        g.append(displayio.TileGrid(bm, pixel_shader=pal, x=bx, y=y))
        _bot_pals.append(pal)

    # RED ALERT text
    al = label.Label(terminalio.FONT, text="RED ALERT", color=0xFF0000, scale=3)
    al.x = (240 - 9 * 18) // 2; al.y = MID_Y
    g.append(al)

    _group = g
    _built = True
# Brightness ramp: smooth but tighter peak
_BRIGHT = [0xFF0000, 0xCC0000, 0x770000, 0x440000, 0x220000, 0x110000]

def render():
    global _built
    if not _built:
        _build()
        display.set_pixel(0xFF0000, brightness=1.0)
        display.draw(_group)
        return

    now = time.monotonic()
    nt = len(_top_pals)
    nb = len(_bot_pals)
    if nt == 0:
        return

    # Sweep position: 0→1 over 1.2s, wrapping
    frac = (now % 1.2) / 1.2

    # Top bars: sweep downward (toward center) — pos moves 0→nt
    pos_t = frac * nt
    for i in range(nt):
        dist = abs(i - pos_t)
        if dist > nt / 2:
            dist = nt - dist
        idx = min(int(dist), len(_BRIGHT) - 1)
        _top_pals[i][0] = _BRIGHT[idx]

    # Bottom bars: sweep upward (toward center) — same direction as top index
    pos_b = frac * nb
    for i in range(nb):
        dist = abs(i - pos_b)
        if dist > nb / 2:
            dist = nb - dist
        idx = min(int(dist), len(_BRIGHT) - 1)
        _bot_pals[i][0] = _BRIGHT[idx]

    display.draw(_group)