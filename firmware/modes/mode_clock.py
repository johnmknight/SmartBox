# modes/mode_clock.py
import displayio, terminalio, time, rtc
from adafruit_display_text import label
import display, settings

_ntp_synced = False
DAYS   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
MONTHS = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def sync_ntp(pool):
    global _ntp_synced
    try:
        import adafruit_ntp
        ntp = adafruit_ntp.NTP(pool, tz_offset=settings.get("timezone_offset",0), cache_seconds=3600)
        rtc.RTC().datetime = ntp.datetime
        _ntp_synced = True; print("[clock] NTP synced")
    except Exception as e: print(f"[clock] NTP failed: {e}")

def render():
    now = time.localtime()
    g = displayio.Group()
    bm=displayio.Bitmap(240,135,1); pal=displayio.Palette(1); pal[0]=0x000000
    g.append(displayio.TileGrid(bm,pixel_shader=pal))

    h = now.tm_hour; m = now.tm_min; s = now.tm_sec
    ampm = "AM" if h<12 else "PM"; h12 = h%12 or 12
    ts = f"{h12:02d}:{m:02d}"
    tl = label.Label(terminalio.FONT, text=ts, color=0x00D4FF, scale=4)
    tl.x=(240-len(ts)*24)//2; tl.y=50; g.append(tl)

    sl = label.Label(terminalio.FONT, text=f"{ampm} :{s:02d}", color=0x666666, scale=1)
    sl.x=165; sl.y=50; g.append(sl)

    try: ds = f"{DAYS[now.tm_wday]}  {MONTHS[now.tm_mon]} {now.tm_mday}, {now.tm_year}"
    except: ds = "Date unavailable"
    dl = label.Label(terminalio.FONT, text=ds, color=0xAAAAAA, scale=1)
    dl.x=(240-len(ds)*6)//2; dl.y=100; g.append(dl)

    nl = label.Label(terminalio.FONT, text="NTP ●" if _ntp_synced else "NTP ○",
                     color=0x00FF80 if _ntp_synced else 0x555555, scale=1)
    nl.x=190; nl.y=122; g.append(nl)

    ml = label.Label(terminalio.FONT, text="CLOCK", color=0x333333, scale=1)
    ml.x=8; ml.y=122; g.append(ml)
    display.draw(g)
