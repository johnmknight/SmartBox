# modes/interrupts/red_alert.py
import displayio, terminalio, time
from adafruit_display_text import label
import display, settings

_phase=0; _last_pulse=0; _PULSE_RATE=0.5

def render():
    global _phase, _last_pulse
    now=time.monotonic()
    if now-_last_pulse>=_PULSE_RATE:
        _phase=1-_phase; _last_pulse=now
        display.set_pixel(0xFF0000 if _phase else 0x440000, brightness=1.0 if _phase else 0.2)
    g=displayio.Group()
    bm=displayio.Bitmap(240,135,1); pal=displayio.Palette(1)
    pal[0]=0xFF0000 if _phase else 0x220000
    g.append(displayio.TileGrid(bm,pixel_shader=pal))
    al=label.Label(terminalio.FONT,text="RED ALERT",color=0xFFFFFF,scale=3)
    al.x=(240-9*18)//2; al.y=50; g.append(al)
    bl=label.Label(terminalio.FONT,text=settings.display_name(),color=0xFFAAAA,scale=1)
    bl.x=(240-len(settings.display_name())*6)//2; bl.y=100; g.append(bl)
    display.draw(g)
