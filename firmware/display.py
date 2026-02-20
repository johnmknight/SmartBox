# display.py
# TFT display manager for ESP32-S3 Reverse TFT Feather.
# 240x135 IPS, ST7789. Buttons: D0=UP, D1=OK, D2=DOWN.
# Required: circup install adafruit_st7789 adafruit_display_text neopixel

import board
import time
import displayio
import terminalio
import neopixel
from fourwire import FourWire
from digitalio import DigitalInOut, Direction, Pull
from adafruit_display_text import label
import settings

# -- Display init --
displayio.release_displays()
tft_cs  = board.TFT_CS
tft_dc  = board.TFT_DC
tft_rst = board.TFT_RESET
tft_bl  = board.TFT_BACKLIGHT
spi     = board.SPI()
display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst)

from adafruit_st7789 import ST7789
display = ST7789(display_bus, rotation=270, width=240, height=135, rowstart=40, colstart=53)

_backlight = DigitalInOut(tft_bl)
_backlight.direction = Direction.OUTPUT
_backlight.value = True

_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)

# -- Buttons --
_btn = {}
for name, pin in [("UP", board.D0), ("OK", board.D1), ("DOWN", board.D2)]:
    b = DigitalInOut(pin)
    b.direction = Direction.INPUT
    b.pull = Pull.UP
    _btn[name] = b

_btn_last  = {"UP": True, "OK": True, "DOWN": True}
_hold_start = {}

# -- Modes --
MODE_TOOLBOX = "TOOLBOX"
MODE_CLOCK   = "CLOCK"
MODE_WEATHER = "WEATHER"
MODE_BATTERY = "BATTERY"
_MODE_ORDER  = [MODE_TOOLBOX, MODE_CLOCK, MODE_WEATHER, MODE_BATTERY]

# -- Interrupts --
INTERRUPT_NONE         = None
INTERRUPT_RED_ALERT    = "RED_ALERT"
INTERRUPT_LOCKDOWN     = "LOCKDOWN"
INTERRUPT_SELF_DESTRUCT = "SELF_DESTRUCT"

# -- State --
_current_mode      = MODE_TOOLBOX
_current_interrupt = INTERRUPT_NONE
_nav_active        = False
_nav_timeout       = 0

# -- Colors --
WHITE   = 0xFFFFFF
BLACK   = 0x000000
CYAN    = 0x00D4FF
AMBER   = 0xF59E0B
GREEN   = 0x00FF80
RED     = 0xFF0000
DIMGRAY = 0x444444

def init():
    _show_boot()
    print(f"[display] Ready - mode={_current_mode}")

def poll_buttons():
    global _btn_last, _hold_start
    events = []
    now = time.monotonic()
    for name, btn in _btn.items():
        current_val = btn.value
        last_val    = _btn_last[name]
        if not current_val and last_val:
            _hold_start[name] = now
        elif current_val and not last_val:
            held = now - _hold_start.get(name, now)
            events.append(f"{name}_HOLD" if held >= 2.0 else f"{name}_PRESS")
            _hold_start.pop(name, None)
        _btn_last[name] = current_val
    return events

def handle_button(event):
    global _current_mode, _nav_active, _nav_timeout
    if _current_interrupt is not None:
        return
    if event in ("UP_PRESS", "DOWN_PRESS"):
        idx = _MODE_ORDER.index(_current_mode)
        if event == "UP_PRESS":
            idx = (idx - 1) % len(_MODE_ORDER)
        else:
            idx = (idx + 1) % len(_MODE_ORDER)
        _current_mode = _MODE_ORDER[idx]
        _nav_active = True
        _nav_timeout = time.monotonic() + 2.0
        print(f"[display] Mode -> {_current_mode}")
        _render_nav_overlay()
    elif event == "OK_PRESS":
        # Quick identify flash
        set_pixel(WHITE, brightness=1.0)
        time.sleep(0.3)
        set_pixel(GREEN)

def nav_active():
    global _nav_active
    if _nav_active and time.monotonic() > _nav_timeout:
        _nav_active = False
    return _nav_active

def _render_nav_overlay():
    """Full-screen mode picker shown during nav mode."""
    _LABELS = {
        MODE_TOOLBOX: ("TOOLBOX", "Status & QR"),
        MODE_CLOCK:   ("CLOCK",   "Time & Date"),
        MODE_WEATHER: ("WEATHER", "Conditions"),
        MODE_BATTERY: ("BATTERY", "Power stats"),
    }
    g = displayio.Group()
    # Dark background
    bm = displayio.Bitmap(240, 135, 1)
    pal = displayio.Palette(1); pal[0] = 0x08090C
    g.append(displayio.TileGrid(bm, pixel_shader=pal))
    # Header
    hdr = label.Label(terminalio.FONT, text="SELECT MODE", color=AMBER, scale=1)
    hdr.x = 76; hdr.y = 8
    g.append(hdr)
    # Divider
    div_bm = displayio.Bitmap(240, 1, 1)
    div_pal = displayio.Palette(1); div_pal[0] = AMBER
    g.append(displayio.TileGrid(div_bm, pixel_shader=div_pal, x=0, y=16))
    # Mode list
    for i, mode in enumerate(_MODE_ORDER):
        selected = (mode == _current_mode)
        y = 26 + i * 26
        if selected:
            # Highlight bar
            sel_bm = displayio.Bitmap(240, 22, 1)
            sel_pal = displayio.Palette(1); sel_pal[0] = 0x001A2A
            g.append(displayio.TileGrid(sel_bm, pixel_shader=sel_pal, x=0, y=y - 4))
            # Cyan left bar
            bar_bm = displayio.Bitmap(3, 22, 1)
            bar_pal = displayio.Palette(1); bar_pal[0] = CYAN
            g.append(displayio.TileGrid(bar_bm, pixel_shader=bar_pal, x=0, y=y - 4))
            arrow = label.Label(terminalio.FONT, text=">", color=CYAN, scale=1)
            arrow.x = 6; arrow.y = y + 2
            g.append(arrow)
        name, sub = _LABELS.get(mode, (mode, ""))
        name_lbl = label.Label(terminalio.FONT, text=name, color=CYAN if selected else WHITE, scale=1)
        name_lbl.x = 18; name_lbl.y = y
        g.append(name_lbl)
        sub_lbl = label.Label(terminalio.FONT, text=sub, color=0x445566, scale=1)
        sub_lbl.x = 18; sub_lbl.y = y + 11
        g.append(sub_lbl)
    # Footer hint
    hint = label.Label(terminalio.FONT, text="UP/DN=CYCLE  OK=FLASH", color=DIMGRAY, scale=1)
    hint.x = 20; hint.y = 128
    g.append(hint)
    display.root_group = g

def set_mode(mode):
    global _current_mode
    if mode in _MODE_ORDER:
        _current_mode = mode

def current_mode():
    return _current_mode

def set_interrupt(interrupt_type):
    global _current_interrupt
    _current_interrupt = interrupt_type
    print(f"[display] Interrupt  {interrupt_type}")
    colors = {INTERRUPT_RED_ALERT: RED, INTERRUPT_LOCKDOWN: AMBER, INTERRUPT_SELF_DESTRUCT: RED}
    set_pixel(colors.get(interrupt_type, WHITE), brightness=1.0)

def clear_interrupt():
    global _current_interrupt
    _current_interrupt = INTERRUPT_NONE
    set_pixel(GREEN)
    print("[display] Interrupt cleared")

def is_interrupted():
    return _current_interrupt is not None

def draw(group):
    display.root_group = group

def set_pixel(color, brightness=0.1):
    _pixel.brightness = brightness
    _pixel[0] = color

def backlight(on=True):
    _backlight.value = on

def _show_boot():
    group = displayio.Group()
    bm = displayio.Bitmap(240, 135, 1)
    pal = displayio.Palette(1)
    pal[0] = BLACK
    group.append(displayio.TileGrid(bm, pixel_shader=pal))
    t = label.Label(terminalio.FONT, text="SMART TOOLBOX", color=CYAN, scale=2)
    t.x = 20; t.y = 40
    group.append(t)
    s = label.Label(terminalio.FONT, text=settings.display_name(), color=WHITE, scale=1)
    s.x = 80; s.y = 80
    group.append(s)
    v = label.Label(terminalio.FONT, text="STB v1.0", color=DIMGRAY, scale=1)
    v.x = 85; v.y = 115
    group.append(v)
    display.root_group = group
    set_pixel(CYAN, brightness=0.3)
    time.sleep(1.5)
