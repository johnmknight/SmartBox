# modes/mode_toolbox.py - Main status display
import displayio, terminalio
from adafruit_display_text import label
import adafruit_miniqr
import display, power, mqtt_client, settings

_category = "Unassigned"

def set_category(cat): global _category; _category = cat
def current_category(): return _category

def _rect(w, h, color):
    bm = displayio.Bitmap(w, h, 1)
    pal = displayio.Palette(1); pal[0] = color
    return bm, pal

def render(state):
    state_color = {"DOCKED":0x00FF80,"AWAY":0xFF8C00,"SET_DOWN":0xFFFF00,"DOCKING":0x00D4FF}.get(state, 0xFFFFFF)
    g = displayio.Group()

    # Background
    bm, pal = _rect(240, 135, 0x000000)
    g.append(displayio.TileGrid(bm, pixel_shader=pal))

    # Header: box name left, state right
    n = label.Label(terminalio.FONT, text=settings.display_name(), color=0xAAAAAA, scale=1)
    n.x = 8; n.y = 12; g.append(n)
    s = label.Label(terminalio.FONT, text=f"[ {state} ]", color=state_color, scale=1)
    s.x = 140; s.y = 12; g.append(s)

    # Green divider lines
    DIV_Y_TOP = 22
    DIV_Y_BOT = 112
    CONTENT_H = DIV_Y_BOT - DIV_Y_TOP  # 90px

    bm, pal = _rect(240, 1, 0x00FF80)
    g.append(displayio.TileGrid(bm, pixel_shader=pal, x=0, y=DIV_Y_TOP))
    bm, pal = _rect(240, 1, 0x00FF80)
    g.append(displayio.TileGrid(bm, pixel_shader=pal, x=0, y=DIV_Y_BOT))

    # QR code square on far right
    SQ = CONTENT_H  # 90x90
    SQ_X = 240 - SQ  # x=150

    try:
        url = f"http://192.168.4.47:8091/box/{settings.box_id()}"
        qr = adafruit_miniqr.QRCode(qr_type=3, error_correct=adafruit_miniqr.L)
        qr.add_data(url.encode("utf-8"))
        qr.make()
        matrix = qr.matrix
        modules = matrix.width
        cell = SQ // modules  # fill the square
        offset = (SQ - modules * cell) // 2  # center remainder

        qr_bm = displayio.Bitmap(SQ, SQ, 2)
        qr_pal = displayio.Palette(2)
        qr_pal[0] = 0xFFFFFF
        qr_pal[1] = 0x000000

        for y in range(modules):
            for x in range(modules):
                if matrix[x, y]:
                    px = offset + x * cell
                    py = offset + y * cell
                    for dy in range(cell):
                        for dx in range(cell):
                            if px+dx < SQ and py+dy < SQ:
                                qr_bm[px+dx, py+dy] = 1

        g.append(displayio.TileGrid(qr_bm, pixel_shader=qr_pal, x=SQ_X, y=DIV_Y_TOP + 1))

    except Exception as e:
        bm, pal = _rect(SQ, SQ, 0x111111)
        g.append(displayio.TileGrid(bm, pixel_shader=pal, x=SQ_X, y=DIV_Y_TOP + 1))
        print(f"[qr] Error: {e}")

    # Text zone: left of square, x=8 to SQ_X-8
    TEXT_MAX_X = SQ_X - 8

    if _category in ("Unassigned", "", None):
        top, bot = "?????", None
    elif "/" in _category:
        parts = _category.split("/", 1)
        top = parts[0].strip().upper()
        bot = parts[1].strip().upper()
    else:
        top = _category.upper()
        bot = None

    # Top line - left justified, scale=2 to stay left of square
    top_text = top if len(top) <= 11 else top[:10] + "…"
    c = label.Label(terminalio.FONT, text=top_text, color=0xFFFFFF, scale=2)
    c.x = 8; c.y = 52 if bot else 67
    g.append(c)

    # Bottom line - group label, left justified, smaller
    if bot:
        bot_text = bot if len(bot) <= 18 else bot[:17] + "…"
        b = label.Label(terminalio.FONT, text=bot_text, color=0x888888, scale=1)
        b.x = 8; b.y = 88
        g.append(b)

    # Status bar
    pct = power.battery_percent()
    bt = f"{chr(0x2B) if power.is_charging() else ''}{pct:.0f}%" if pct >= 0 else "---"
    bl = label.Label(terminalio.FONT, text=bt, color=0x00FF80 if pct > 20 else 0xFF4444, scale=1)
    bl.x = 8; bl.y = 122; g.append(bl)

    mc = 0x00D4FF if mqtt_client.is_connected() else 0x555555
    ml = label.Label(terminalio.FONT, text="MQTT", color=mc, scale=1)
    ml.x = 190; ml.y = 122; g.append(ml)

    display.draw(g)
