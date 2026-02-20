# modes/interrupts/self_destruct.py
import displayio, terminalio, time
from adafruit_display_text import label
import display, settings

_start=0; _duration=30; _active=False

def start(seconds=30):
    global _start,_duration,_active
    _duration=seconds; _start=time.monotonic(); _active=True
    print(f"[self_destruct] Countdown: {seconds}s")

def render():
    global _active
    if not _active: return False
    elapsed=time.monotonic()-_start; remaining=max(0,_duration-elapsed)
    if remaining<=0:
        _active=False; _render_done(); return True
    ratio=remaining/_duration
    color=0xFF8C00 if ratio>0.5 else (0xFF4400 if ratio>0.2 else 0xFF0000)
    bg=0x1A0800 if ratio>0.5 else (0x1A0400 if ratio>0.2 else 0x1A0000)
    if remaining<10:
        pulse=int(time.monotonic()*4)%2
        display.set_pixel(0xFF0000 if pulse else 0x000000, brightness=1.0)
    else: display.set_pixel(color, brightness=0.5)
    g=displayio.Group()
    bm=displayio.Bitmap(240,135,1); pal=displayio.Palette(1); pal[0]=bg
    g.append(displayio.TileGrid(bm,pixel_shader=pal))
    hl=label.Label(terminalio.FONT,text="SELF DESTRUCT",color=0xFF4400,scale=1)
    hl.x=(240-13*6)//2; hl.y=15; g.append(hl)
    cs=f"{int(remaining):02d}"
    cl=label.Label(terminalio.FONT,text=cs,color=color,scale=5)
    cl.x=(240-len(cs)*30)//2; cl.y=65; g.append(cl)
    tl=label.Label(terminalio.FONT,text=f".{int((remaining%1)*10)}",color=0x443300,scale=2)
    tl.x=165; tl.y=80; g.append(tl)
    nl=label.Label(terminalio.FONT,text=settings.display_name(),color=0x442200,scale=1)
    nl.x=(240-len(settings.display_name())*6)//2; nl.y=118; g.append(nl)
    display.draw(g); return False

def _render_done():
    for _ in range(3):
        display.set_pixel(0xFFFFFF,brightness=1.0); time.sleep(0.1)
        display.set_pixel(0x000000,brightness=0); time.sleep(0.1)
    g=displayio.Group()
    bm=displayio.Bitmap(240,135,1); pal=displayio.Palette(1); pal[0]=0x000000
    g.append(displayio.TileGrid(bm,pixel_shader=pal))
    dl=label.Label(terminalio.FONT,text="DETONATED",color=0x440000,scale=2)
    dl.x=(240-9*12)//2; dl.y=60; g.append(dl)
    display.draw(g); time.sleep(2.0)
