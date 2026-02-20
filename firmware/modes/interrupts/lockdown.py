# modes/interrupts/lockdown.py
import displayio, terminalio
from adafruit_display_text import label
import display, settings

def render():
    g=displayio.Group()
    bm=displayio.Bitmap(240,135,1); pal=displayio.Palette(1); pal[0]=0x2A1A00
    g.append(displayio.TileGrid(bm,pixel_shader=pal))
    ll=label.Label(terminalio.FONT,text="LOCKDOWN",color=0xF59E0B,scale=3)
    ll.x=(240-8*18)//2; ll.y=45; g.append(ll)
    il=label.Label(terminalio.FONT,text=settings.box_id().upper(),color=0x886600,scale=2)
    il.x=(240-len(settings.box_id())*12)//2; il.y=85; g.append(il)
    sl=label.Label(terminalio.FONT,text="SECURE AND HOLD",color=0x554400,scale=1)
    sl.x=(240-15*6)//2; sl.y=115; g.append(sl)
    display.draw(g)
