# modes/mode_battery.py
import displayio, terminalio
from adafruit_display_text import label
import display, power

def render():
    g = displayio.Group()
    bm=displayio.Bitmap(240,135,1); pal=displayio.Palette(1); pal[0]=0x000000
    g.append(displayio.TileGrid(bm,pixel_shader=pal))
    ml=label.Label(terminalio.FONT,text="BATTERY",color=0x333333,scale=1)
    ml.x=8; ml.y=12; g.append(ml)

    pct=power.battery_percent(); v=power.battery_voltage()
    charging=power.is_charging(); usb=power.usb_connected(); low=power.is_low_battery()

    if pct>=0:
        pc=0xFF4444 if low else (0xFFFF00 if pct<50 else 0x00FF80)
        ps=f"{pct:.0f}%"
    else: pc=0x555555; ps="---"
    pl=label.Label(terminalio.FONT,text=ps,color=pc,scale=4)
    pl.x=(240-len(ps)*24)//2; pl.y=55; g.append(pl)

    # Battery bar
    BAR_X,BAR_Y,BAR_W,BAR_H=20,72,200,8
    tbm=displayio.Bitmap(BAR_W,BAR_H,1); tpal=displayio.Palette(1); tpal[0]=0x222222
    g.append(displayio.TileGrid(tbm,pixel_shader=tpal,x=BAR_X,y=BAR_Y))
    if pct>0:
        fw=max(1,int(BAR_W*min(pct,100)/100))
        fbm=displayio.Bitmap(fw,BAR_H,1); fpal=displayio.Palette(1)
        fpal[0]=0xFF4444 if pct<20 else (0xFFFF00 if pct<50 else 0x00FF80)
        g.append(displayio.TileGrid(fbm,pixel_shader=fpal,x=BAR_X,y=BAR_Y))

    if charging: st="Charging via USB"; sc=0x00D4FF
    elif usb: st="USB connected"; sc=0x00FF80
    else: st="On battery"; sc=0xAAAAAA
    sl=label.Label(terminalio.FONT,text=st,color=sc,scale=1)
    sl.x=(240-len(st)*6)//2; sl.y=95; g.append(sl)

    vs=f"{v:.2f}V" if v>=0 else "-.--V"
    try:
        import wifi; rs=f"WiFi {wifi.radio.ap_info.rssi}dBm"
    except: rs="WiFi ---"
    dl=label.Label(terminalio.FONT,text=f"{vs}   {rs}",color=0x444444,scale=1)
    dl.x=40; dl.y=122; g.append(dl)
    display.draw(g)
