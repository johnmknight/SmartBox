# modes/mode_toolbox.py — Main status display
import displayio, terminalio, time
from adafruit_display_text import label
import display, power, mqtt_client, settings

_category = "Unassigned"

def set_category(cat): global _category; _category = cat
def current_category(): return _category

def render(state):
    state_color = {"DOCKED":0x00FF80,"AWAY":0xFF8C00,"SET_DOWN":0xFFFF00,"DOCKING":0x00D4FF}.get(state,0xFFFFFF)
    g = displayio.Group()
    bm = displayio.Bitmap(240,135,1); pal = displayio.Palette(1); pal[0]=0x000000
    g.append(displayio.TileGrid(bm,pixel_shader=pal))

    n = label.Label(terminalio.FONT, text=settings.display_name(), color=0xAAAAAA, scale=1)
    n.x=8; n.y=12; g.append(n)

    s = label.Label(terminalio.FONT, text=f"[ {state} ]", color=state_color, scale=1)
    s.x=140; s.y=12; g.append(s)

    div_bm=displayio.Bitmap(224,1,1); div_pal=displayio.Palette(1); div_pal[0]=0x333333
    g.append(displayio.TileGrid(div_bm,pixel_shader=div_pal,x=8,y=22))

    cat = _category if len(_category)<=18 else _category[:17]+"…"
    c = label.Label(terminalio.FONT, text=cat, color=0xFFFFFF, scale=2)
    c.x=max(8,(240-len(cat)*12)//2); c.y=65; g.append(c)

    pct = power.battery_percent()
    bt = f"{'⚡' if power.is_charging() else ''}{pct:.0f}%" if pct>=0 else "---"
    bl = label.Label(terminalio.FONT, text=bt, color=0x00FF80 if pct>20 else 0xFF4444, scale=1)
    bl.x=8; bl.y=122; g.append(bl)

    ms = "MQTT ●" if mqtt_client.is_connected() else "MQTT ○"
    mc = 0x00D4FF if mqtt_client.is_connected() else 0x555555
    ml = label.Label(terminalio.FONT, text=ms, color=mc, scale=1)
    ml.x=170; ml.y=122; g.append(ml)
    display.draw(g)
