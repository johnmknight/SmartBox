import time, json, threading, requests
import paho.mqtt.client as mqttlib
from paho.mqtt.enums import CallbackAPIVersion

HA_URL    = "http://192.168.4.51:8123"
HA_TOKEN  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjNmVkYmNkNzJjMjQ0N2M0OWQ4MGU3MTFhOTFjMjQyNyIsImlhdCI6MTc3MTYzNDM2NiwiZXhwIjoyMDg2OTk0MzY2fQ.DoJQLPvw70_RC-Os4FvGrlktErQeRkxyfdJ4QIcZfBI"
HA_ENTITY = "weather.weather_home"
INTERVAL  = 600

_boxes  = []
_broker = "192.168.4.47"
_port   = 1883

def init(broker: str, port: int, boxes: list):
    global _boxes, _broker, _port
    _boxes = boxes; _broker = broker; _port = port
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()
    print(f"[weather] Poller started -> {boxes}")

def _poll_loop():
    while True:
        _fetch_and_publish()
        time.sleep(INTERVAL)

def _fetch_and_publish():
    try:
        r = requests.get(
            f"{HA_URL}/api/states/{HA_ENTITY}",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            timeout=10
        )
        r.raise_for_status()
        data = r.json(); attrs = data.get("attributes", {})
        payload = {
            "condition":  data.get("state", "unknown"),
            "temp":       round(attrs.get("temperature", 0)),
            "feels_like": round(attrs.get("dew_point", 0)),
            "humidity":   round(attrs.get("humidity", 0)),
            "wind":       round(attrs.get("wind_speed", 0)),
            "location":   attrs.get("friendly_name", "Home"),
        }
        msg = json.dumps(payload)
        c = mqttlib.Client(CallbackAPIVersion.VERSION2, client_id="stb_weather_poller")
        c.connect(_broker, _port)
        for box_id in _boxes:
            topic = f"smarttoolbox/{box_id}/weather"
            c.publish(topic, msg)
            print(f"[weather] -> {topic}: {payload['condition']} {payload['temp']}F")
        c.disconnect()
    except Exception as e:
        print(f"[weather] Error: {e}")
