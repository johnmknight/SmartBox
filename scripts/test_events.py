#!/usr/bin/env python3
"""
SmartToolbox Event Tester
Publishes Marchog interrupt events via MQTT for dev/testing.

Usage:
    python test_events.py red
    python test_events.py lockdown
    python test_events.py destruct [seconds]
    python test_events.py clear
    python test_events.py          (interactive menu)
"""

import sys, json, time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

BROKER = "192.168.4.47"
PORT   = 1883

EVENTS = {
    "red":      ("marchog/event/red-alert",      {}),
    "lockdown": ("marchog/event/lockdown",        {}),
    "destruct": ("marchog/event/self-destruct",   {"countdown": 30}),
    "clear":    ("marchog/event/all-clear",       {}),
}

def publish(topic, payload):
    c = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="stb_test_events")
    c.connect(BROKER, PORT)
    c.publish(topic, json.dumps(payload))
    c.disconnect()
    print(f"  -> {topic}: {payload}")

def interactive():
    while True:
        print("\n=== SmartToolbox Event Tester ===")
        print("  1) Red Alert")
        print("  2) Lockdown")
        print("  3) Self Destruct (30s)")
        print("  4) All Clear")
        print("  5) Weather push (test)")
        print("  q) Quit")
        ch = input("\n> ").strip().lower()
        if ch in ("q", "quit", "exit"):
            break
        elif ch == "1":
            publish(*EVENTS["red"])
        elif ch == "2":
            publish(*EVENTS["lockdown"])
        elif ch == "3":
            secs = input("  Countdown seconds [30]: ").strip()
            secs = int(secs) if secs else 30
            publish("marchog/event/self-destruct", {"countdown": secs})
        elif ch == "4":
            publish(*EVENTS["clear"])
        elif ch == "5":
            publish("smarttoolbox/box-01/weather", {
                "condition": "sunny", "temp": 72, "feels_like": 68,
                "humidity": 65, "wind": 8, "location": "Home"
            })
        else:
            print("  ???")

def main():
    args = sys.argv[1:]
    if not args:
        interactive()
        return

    cmd = args[0].lower()
    if cmd not in EVENTS:
        print(f"Unknown: {cmd}")
        print(f"Options: {', '.join(EVENTS.keys())}")
        return

    topic, payload = EVENTS[cmd]
    if cmd == "destruct" and len(args) > 1:
        payload = {"countdown": int(args[1])}

    publish(topic, payload)

if __name__ == "__main__":
    main()