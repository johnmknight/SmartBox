# sensor.py
# VCNL4020 proximity sensor wrapper.
# Sensor points DOWN - short distance = box is resting on a surface.
# Required: circup install adafruit_vcnl4020

import time
import board
import settings

try:
    import adafruit_vcnl4020
    _LIBRARY_AVAILABLE = True
except ImportError:
    print("[sensor] WARNING: adafruit_vcnl4020 not installed - using simulated values")
    _LIBRARY_AVAILABLE = False

_sensor = None
_last_raw = 0
_on_surface = False
_sample_buffer = []

def init():
    global _sensor
    if not _LIBRARY_AVAILABLE:
        print("[sensor] Running in simulation mode")
        return False
    try:
        i2c = board.STEMMA_I2C()
        _sensor = adafruit_vcnl4020.VCNL4020(i2c)
        print(f"[sensor] VCNL4020 ready (threshold={settings.prox_threshold()})")
        return True
    except Exception as e:
        print(f"[sensor] ERROR: {e}")
        _sensor = None
        return False

def read_raw():
    global _last_raw
    if _sensor is None:
        return 2500  # simulated "on surface"
    try:
        _last_raw = _sensor.proximity
        return _last_raw
    except Exception as e:
        print(f"[sensor] Read error: {e}")
        return _last_raw

def read_averaged():
    global _sample_buffer
    samples = settings.prox_samples()
    _sample_buffer.append(read_raw())
    if len(_sample_buffer) > samples:
        _sample_buffer.pop(0)
    return sum(_sample_buffer) // len(_sample_buffer)

def is_on_surface():
    global _on_surface
    raw = read_averaged()
    _on_surface = raw >= settings.prox_threshold()
    return _on_surface

def read_lux():
    if _sensor is None:
        return 0.0
    try:
        return _sensor.lux
    except Exception as e:
        print(f"[sensor] Lux read error: {e}")
        return 0.0

def debug_payload():
    return {
        "proximity_raw": _last_raw,
        "proximity_avg": read_averaged(),
        "on_surface": _on_surface,
        "lux": read_lux(),
        "threshold": settings.prox_threshold(),
    }
