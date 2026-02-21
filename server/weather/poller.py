import time, threading, requests
from server.mqtt import listener

HA_URL    = "http://192.168.4.51:8123"
HA_TOKEN  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjNmVkYmNkNzJjMjQ0N2M0OWQ4MGU3MTFhOTFjMjQyNyIsImlhdCI6MTc3MTYzNDM2NiwiZXhwIjoyMDg2OTk0MzY2fQ.DoJQLPvw70_RC-Os4FvGrlktErQeRkxyfdJ4QIcZfBI"
HA_ENTITY = "weather.weather_home"
INTERVAL  = 600

_boxes = []

def init(boxes: list):
    global _boxes
    _boxes = boxes
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()
    print(f"[weather] Poller started - pushing to {boxes}")

def _poll_loop():
    time.sleep(3)  # wait for listener MQTT to connect first
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
        data  = r.json()
        attrs = data.get("attributes", {})
        payload = {
            "condition":  data.get("state", "unknown"),
            "temp":       round(attrs.get("temperature", 0)),
            "feels_like": round(attrs.get("dew_point", 0)),
            "humidity":   round(attrs.get("humidity", 0)),
            "wind":       round(attrs.get("wind_speed", 0)),
            "location":   attrs.get("friendly_name", "Home"),
        }
        for box_id in _boxes:
            topic = f"smarttoolbox/{box_id}/weather"
            listener.publish(topic, payload)
            print(f"[weather] -> {topic}: {payload['condition']} {payload['temp']}F")
    except Exception as e:
        print(f"[weather] Fetch error: {e}")
