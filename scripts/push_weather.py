import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import json, time
time.sleep(3)
c = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="test_wx")
c.connect("192.168.4.47", 1883)
c.publish("smarttoolbox/box-01/weather", json.dumps({
    "condition": "sunny", "temp": 72, "feels_like": 68,
    "humidity": 65, "wind": 8, "location": "Home"
}))
c.disconnect()
print("pushed")