import time, json, threading, requests
import paho.mqtt.client as mqtt

HA_URL    = "http://192.168.4.51:8123"
HA_TOKEN  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjNmVkYmNkNzJjMjQ0N2M0OWQ4MGU3MTFhOTFjMjQyNyIsImlhdCI6MTc3MTYzNDM2NiwiZXhwIjoyMDg2OTk0MzY2fQ.DoJQLPvw70_RC-Os4FvGrlktErQeRkxyfdJ4QIcZfBI"
HA_ENTITY = "weather.weather_home"
INTERVAL  = 600  # seconds

_mqtt_client = None
_boxes       = []

def init(mqtt_broker: str, mqtt_port: int, boxes: list):
    global _mqtt_client, _boxes
    _boxes = boxes
    _mqtt_client = mqtt.Client(client_id="stb_weather_poller")
    _mqtt_client.connect(mqtt_broker, mqtt_port)
    _mqtt_client.loop_start()
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()
    print(f"[weather] Poller started - pushing to {boxes}")

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
        msg = json.dumps(payload)
        for box_id in _boxes:
            topic = f"smarttoolbox/{box_id}/weather"
            _mqtt_client.publish(topic, msg)
            print(f"[weather] -> {topic}: {payload['condition']} {payload['temp']}F")
    except Exception as e:
        print(f"[weather] Fetch error: {e}")
