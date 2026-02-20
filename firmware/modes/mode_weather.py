# modes/mode_weather.py - Weather pushed from server via MQTT
import displayio, terminalio, time
from adafruit_display_text import label
import display, settings

_weather = None
_updated_at = 0

def update(payload):
    global _weather, _updated_at
    _weather = payload; _updated_at = time.monotonic()
    print(f"[weather] {payload.get('condition','')} {payload.get('temp','')}")

def render():
    g = displayio.Group()
    bm=displayio.Bitmap(240,135,1); pal=displayio.Palette(1); pal[0]=0x000000
    g.append(displayio.TileGrid(bm,pixel_shader=pal))
    ml = label.Label(terminalio.FONT, text="WEATHER", color=0x333333, scale=1)
    ml.x=8; ml.y=12; g.append(ml)

    if _weather is None:
        nl = label.Label(terminalio.FONT, text="Waiting for server...", color=0x555555, scale=1)
        nl.x=35; nl.y=67; g.append(nl)
    else:
        unit=settings.get("weather_unit","F"); temp=_weather.get("temp","--")
        feels=_weather.get("feels_like","--"); cond=_weather.get("condition","Unknown")
        humid=_weather.get("humidity","--"); loc=_weather.get("location","")
        if loc:
            ll=label.Label(terminalio.FONT,text=loc,color=0x666666,scale=1)
            ll.x=240-len(loc)*6-8; ll.y=12; g.append(ll)
        ts=f"{temp}{unit}"
        tl=label.Label(terminalio.FONT,text=ts,color=0xFFFFFF,scale=4)
        tl.x=10; tl.y=60; g.append(tl)
        cl=label.Label(terminalio.FONT,text=cond,color=0xAAAAAA,scale=1)
        cl.x=140; cl.y=45; g.append(cl)
        dl=label.Label(terminalio.FONT,text=f"Feels {feels}  Humidity {humid}%",color=0x666666,scale=1)
        dl.x=8; dl.y=100; g.append(dl)
        if time.monotonic()-_updated_at > 3600:
            sl=label.Label(terminalio.FONT,text="STALE",color=0xFF4444,scale=1)
            sl.x=190; sl.y=122; g.append(sl)
    display.draw(g)
