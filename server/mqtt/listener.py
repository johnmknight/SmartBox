# server/mqtt/listener.py
# Subscribes to all smarttoolbox/# topics and updates the database.

import os, json, asyncio, threading
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from datetime import datetime, timezone

_broker  = os.getenv("MQTT_BROKER", "127.0.0.1")
_port    = int(os.getenv("MQTT_PORT", 1883))
_user    = os.getenv("MQTT_USER", "") or None
_pass    = os.getenv("MQTT_PASS", "") or None

_db_updater = None   # set by main.py after DB is ready
_client     = None
_loop       = None

def set_db_updater(fn):
    global _db_updater
    _db_updater = fn

def _on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[mqtt-listener] Connected to {_broker}:{_port}")
        client.subscribe("smarttoolbox/#")
        print("[mqtt-listener] Subscribed to smarttoolbox/#")
    else:
        print(f"[mqtt-listener] Connect failed rc={reason_code}")

def _on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        parts = topic.split("/")   # smarttoolbox/<box_id>/<type>
        if len(parts) < 3: return
        box_id    = parts[1]
        msg_type  = parts[2]
        if _db_updater and _loop:
            asyncio.run_coroutine_threadsafe(_db_updater(box_id, msg_type, payload), _loop)
    except Exception as e:
        print(f"[mqtt-listener] Message error: {e}")

def publish(topic, payload):
    if _client:
        _client.publish(topic, json.dumps(payload))

def send_command(box_id, payload):
    publish(f"smarttoolbox/{box_id}/command", payload)

def start(loop):
    global _client, _loop
    _loop = loop
    _client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="stb-server")
    if _user:
        _client.username_pw_set(_user, _pass)
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    def _run():
        try:
            _client.connect(_broker, _port, keepalive=60)
            _client.loop_forever()
        except Exception as e:
            print(f"[mqtt-listener] Failed to connect: {e}")
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[mqtt-listener] Connecting to {_broker}:{_port}...")
