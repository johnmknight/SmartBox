# mqtt_client.py - SmartToolbox MQTT wrapper
# Required: circup install adafruit_minimqtt

import time, json, settings

try:
    import adafruit_minimqtt.adafruit_minimqtt as MQTT
    _LIB = True
except ImportError:
    print("[mqtt] WARNING: adafruit_minimqtt not installed")
    _LIB = False

_BOX = None
_client = None
_connected = False
_last_reconnect = 0
_RECONNECT_INTERVAL = 30
_handlers = {}

TOPIC_COMMAND       = None
TOPIC_WEATHER       = None
TOPIC_CONFIG        = None
TOPIC_RED_ALERT     = "marchog/event/red-alert"
TOPIC_LOCKDOWN      = "marchog/event/lockdown"
TOPIC_SELF_DESTRUCT = "marchog/event/self-destruct"
TOPIC_ALL_CLEAR     = "marchog/event/all-clear"

def _t(suffix): return f"smarttoolbox/{_BOX}/{suffix}"

def init(wifi_pool, ssl_context=None):
    global _client, _BOX, TOPIC_COMMAND, TOPIC_WEATHER, TOPIC_CONFIG
    if not _LIB or not settings.use_mqtt(): return False
    _BOX = settings.box_id()
    TOPIC_COMMAND = _t("command")
    TOPIC_WEATHER = _t("weather")
    TOPIC_CONFIG  = _t("config")
    broker = settings.get("mqtt_broker")
    if not broker: return False
    _client = MQTT.MQTT(
        broker=broker, port=settings.get("mqtt_port", 1883),
        username=settings.get("mqtt_user") or None,
        password=settings.get("mqtt_pass") or None,
        socket_pool=wifi_pool, ssl_context=ssl_context,
        client_id=f"stb_{_BOX}", keep_alive=60,
        socket_timeout=0.1,
    )
    _client.on_connect    = _on_connect
    _client.on_disconnect = _on_disconnect
    _client.on_message    = _on_message
    return _connect()

def on_message(topic, callback): _handlers[topic] = callback

def poll():
    global _connected, _last_reconnect
    if _client is None: return
    if not _connected:
        now = time.monotonic()
        if now - _last_reconnect > _RECONNECT_INTERVAL:
            _last_reconnect = now; _connect()
        return
    try: _client.loop(timeout=0.1)
    except Exception as e:
        print(f"[mqtt] Loop error: {e}"); _connected = False

def publish_state(state, category=None):
    _pub(_t("state"), {"box_id": settings.box_id(), "state": state, "category": category, "ts": time.monotonic()})

def publish_battery(pct, v, charging):
    _pub(_t("battery"), {"box_id": settings.box_id(), "pct": round(pct,1), "voltage": round(v,2), "charging": charging})

def publish_boot():
    _pub(_t("boot"), {"box_id": settings.box_id(), "rack_id": settings.rack_id(), "display_name": settings.display_name(), "version": "1.0.0"})

def publish_ack(event, extra=None):
    p = {"box_id": settings.box_id(), "ack": event}
    if extra: p.update(extra)
    _pub(_t("ack"), p)

def publish_debug(payload):
    if not settings.debug(): return
    payload["box_id"] = settings.box_id()
    _pub(_t("debug"), payload)

def is_connected(): return _connected

def _connect():
    global _connected
    try:
        print(f"[mqtt] Connecting to {settings.get('mqtt_broker')}...")
        _client.connect(); return True
    except Exception as e:
        print(f"[mqtt] Connect failed: {e}"); _connected = False; return False

def _subscribe_all():
    topics = [TOPIC_COMMAND, TOPIC_WEATHER, TOPIC_CONFIG]
    if settings.use_marchog(): topics += [TOPIC_RED_ALERT, TOPIC_LOCKDOWN, TOPIC_SELF_DESTRUCT, TOPIC_ALL_CLEAR]
    for t in topics:
        if t:
            try: _client.subscribe(t); print(f"[mqtt] Subscribed: {t}")
            except Exception as e: print(f"[mqtt] Sub error {t}: {e}")

def _pub(topic, payload):
    if _client is None or not _connected:
        if settings.debug(): print(f"[mqtt] OFFLINE - {topic}: {payload}")
        return
    try: _client.publish(topic, json.dumps(payload))
    except Exception as e: print(f"[mqtt] Publish error: {e}")

def _on_connect(client, userdata, flags, rc):
    global _connected; _connected = True
    print(f"[mqtt] Connected (rc={rc})"); _subscribe_all(); publish_boot()

def _on_disconnect(client, userdata, rc):
    global _connected; _connected = False; print(f"[mqtt] Disconnected (rc={rc})")

def _on_message(client, topic, message):
    print(f"[mqtt]  {topic}: {message}")
    handler = _handlers.get(topic)
    if handler:
        try: handler(topic, json.loads(message))
        except Exception as e: print(f"[mqtt] Handler error {topic}: {e}")
