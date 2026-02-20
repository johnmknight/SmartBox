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
    if event == "OK_HOLD":
        _nav_active = not _nav_active
        _nav_timeout = time.monotonic() + 10
        set_pixel(AMBER if _nav_active else GREEN)
        return
    if _nav_active:
        idx = _MODE_ORDER.index(_current_mode)
        if event == "UP_PRESS":
            idx = (idx - 1) % len(_MODE_ORDER)
        elif event == "DOWN_PRESS":
            idx = (idx + 1) % len(_MODE_ORDER)
        elif event == "OK_PRESS":
            _nav_active = False
            set_pixel(GREEN)
            return
        _current_mode = _MODE_ORDER[idx]
        print(f"[display] Mode  {_current_mode}")
    if _nav_active and time.monotonic() > _nav_timeout:
        _nav_active = False
        set_pixel(GREEN)

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
