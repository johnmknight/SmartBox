# power.py - MAX17048 battery monitor + USB detection
# Required: circup install adafruit_max1704x

import board, supervisor

try:
    import adafruit_max1704x
    _LIB = True
except ImportError:
    print("[power] WARNING: adafruit_max1704x not installed")
    _LIB = False

_gauge = None
_last_usb = False

def init():
    global _gauge
    if not _LIB:
        print("[power] Running without battery gauge")
        return False
    try:
        i2c = board.STEMMA_I2C()
        _gauge = adafruit_max1704x.MAX17048(i2c)
        print(f"[power] MAX17048 ready - {battery_percent():.0f}%")
        return True
    except Exception as e:
        print(f"[power] ERROR: {e}")
        # Scan I2C to see what's actually there
        try:
            i2c = board.STEMMA_I2C()
            if i2c.try_lock():
                found = [hex(a) for a in i2c.scan()]
                i2c.unlock()
                print(f"[power] I2C scan: {found}")
        except Exception as se:
            print(f"[power] I2C scan failed: {se}")
        _gauge = None
        return False

def usb_connected():   return supervisor.runtime.usb_connected

def poll_usb_change():
    global _last_usb
    current = usb_connected()
    if current != _last_usb:
        _last_usb = current
        return "connected" if current else "disconnected"
    return None

def battery_percent():
    if _gauge is None: return -1.0
    try: return _gauge.cell_percent
    except Exception: return -1.0

def battery_voltage():
    if _gauge is None: return -1.0
    try: return _gauge.cell_voltage
    except Exception: return -1.0

def is_charging():     return usb_connected() and battery_percent() < 99.0
def is_low_battery():
    pct = battery_percent()
    return pct >= 0 and pct < 20.0

def debug_payload():
    return {
        "usb_connected": usb_connected(),
        "battery_pct":   battery_percent(),
        "battery_v":     battery_voltage(),
        "charging":      is_charging(),
        "low_battery":   is_low_battery(),
    }
