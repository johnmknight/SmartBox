# modes/mode_weather.py - Weather display with icon
# Weather data pushed from server via MQTT.
# 3-column layout: Temp+Condition | Stats | Icon

import displayio, terminalio, time
from adafruit_display_text import label
import display, settings
import weather_icons

_weather = None
_updated_at = 0

def update(payload):
    global _weather, _updated_at
    _weather = payload; _updated_at = time.monotonic()
    print(f"[weather] {payload.get('condition','')} {payload.get('temp','')}")

def _rect(w, h, color):
    bm = displayio.Bitmap(w, h, 1)
    pal = displayio.Palette(1); pal[0] = color
    return bm, pal
def render():
    g = displayio.Group()

    # Background
    bm, pal = _rect(240, 135, 0x000000)
    g.append(displayio.TileGrid(bm, pixel_shader=pal))

    if _weather is None:
        ml = label.Label(terminalio.FONT, text="WEATHER", color=0x333333, scale=1)
        ml.x = 8; ml.y = 12; g.append(ml)
        nl = label.Label(terminalio.FONT, text="Waiting for data...", color=0x555555, scale=1)
        nl.x = 35; nl.y = 67; g.append(nl)
        display.draw(g)
        return

    unit  = settings.get("weather_unit", "F")
    temp  = _weather.get("temp", "--")
    feels = _weather.get("feels_like", "--")
    cond  = _weather.get("condition", "unknown")
    humid = _weather.get("humidity", "--")
    wind  = _weather.get("wind", "--")
    loc   = _weather.get("location", "")

    # Location in header
    if loc:
        ll = label.Label(terminalio.FONT, text=loc, color=0x555555, scale=1)
        ll.x = 240 - len(loc) * 6 - 8; ll.y = 12; g.append(ll)

    # Green dividers
    DIV_Y_TOP = 22
    DIV_Y_BOT = 112
    bm, pal = _rect(240, 1, 0x00FF80)
    g.append(displayio.TileGrid(bm, pixel_shader=pal, x=0, y=DIV_Y_TOP))
    bm, pal = _rect(240, 1, 0x00FF80)
    g.append(displayio.TileGrid(bm, pixel_shader=pal, x=0, y=DIV_Y_BOT))
    # === 3-COLUMN LAYOUT ===
    # Col 3: Icon 90x90 (x=150)
    SQ = DIV_Y_BOT - DIV_Y_TOP
    SQ_X = 240 - SQ
    icon_tg = weather_icons.tile(cond)
    icon_tg.x = SQ_X; icon_tg.y = DIV_Y_TOP + 1
    g.append(icon_tg)

    # Col 1: Temp (scale=4) + Condition (scale=2)  x=4
    temp_str = f"{temp}\xb0"
    tl = label.Label(terminalio.FONT, text=temp_str, color=0xFFFFFF, scale=4)
    tl.x = 4; tl.y = 45; g.append(tl)

    cond_disp = cond.upper().replace("-", " ")
    if len(cond_disp) > 6:
        cond_disp = cond_disp[:5] + "\u2026"
    cl = label.Label(terminalio.FONT, text=cond_disp, color=0x00D4FF, scale=2)
    cl.x = 4; cl.y = 80; g.append(cl)

    # Col 2: Stats (scale=2, stacked)  x=78
    COL2 = 78
    f1 = label.Label(terminalio.FONT, text=f"FL{feels}\xb0", color=0x666666, scale=2)
    f1.x = COL2; f1.y = 38; g.append(f1)

    h1 = label.Label(terminalio.FONT, text=f"H {humid}%", color=0x666666, scale=2)
    h1.x = COL2; h1.y = 60; g.append(h1)

    w1 = label.Label(terminalio.FONT, text=f"W {wind}", color=0x666666, scale=2)
    w1.x = COL2; w1.y = 82; g.append(w1)

    # Status bar
    age_secs = time.monotonic() - _updated_at
    if age_secs > 3600:
        stale = label.Label(terminalio.FONT, text="STALE", color=0xFF4444, scale=1)
        stale.x = 8; stale.y = 122; g.append(stale)
    else:
        mins = int(age_secs // 60)
        al = label.Label(terminalio.FONT, text=f"{mins}m ago", color=0x333333, scale=1)
        al.x = 8; al.y = 122; g.append(al)

    display.draw(g)