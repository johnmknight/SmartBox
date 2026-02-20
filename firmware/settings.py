# settings.py
# Loads config.json from the Feather's flash filesystem.
# All other modules import from here - never read config.json directly.

import json

_config = None

def load():
    global _config
    try:
        with open("/config.json", "r") as f:
            _config = json.load(f)
        print(f"[settings] Loaded config for {_config.get('box_id', 'unknown')}")
    except OSError:
        print("[settings] ERROR: config.json not found - using defaults")
        _config = _defaults()
    except ValueError as e:
        print(f"[settings] ERROR: config.json parse error: {e} - using defaults")
        _config = _defaults()
    return _config

def get(key, fallback=None):
    if _config is None:
        load()
    return _config.get(key, fallback)

def _defaults():
    return {
        "box_id": "box-unknown",
        "rack_id": "rack-01",
        "display_name": "Box ",
        "wifi_ssid": "",
        "wifi_pass": "",
        "server_url": "",
        "use_mqtt": False,
        "mqtt_broker": "",
        "mqtt_port": 1883,
        "mqtt_user": "",
        "mqtt_pass": "",
        "use_marchog": False,
        "proximity_threshold": 50,
        "proximity_samples": 5,
        "timezone_offset": 0,
        "display_brightness": 1.0,
        "weather_unit": "F",
        "debug": True,
    }

def box_id():         return get("box_id", "box-unknown")
def rack_id():        return get("rack_id", "rack-01")
def display_name():   return get("display_name", "Box ")
def server_url():     return get("server_url", "")
def use_mqtt():       return get("use_mqtt", False)
def use_marchog():    return get("use_marchog", False)
def debug():          return get("debug", True)
def prox_threshold(): return get("proximity_threshold", 50)
def prox_samples():   return get("proximity_samples", 5)
