# SmartToolbox

ESP32-S3 Reverse TFT Feather firmware + server for intelligent tool storage tracking.

## Hardware (per box)
- Adafruit ESP32-S3 Reverse TFT Feather (#5691)
- Adafruit VCNL4020 Proximity + Light Sensor (#5860) via STEMMA QT
- LiPoly battery
- USB-C dock connector (rack-mounted)

## Quick Start

### Firmware
1. Flash CircuitPython 9.x to the Feather
2. `circup install adafruit_minimqtt adafruit_vcnl4020 adafruit_max1704x adafruit_st7789 adafruit_display_text adafruit_ntp neopixel`
3. Edit `firmware/config.json` with your WiFi + server details
4. Copy all `firmware/` files to the Feather's CIRCUITPY drive

### Server
```bash
cp .env.example .env  # edit as needed
pip install -r requirements.txt
python server/main.py
```

## Deployment Scenarios
- **Standalone** — no MQTT config needed, embedded broker starts automatically
- **+ Home Assistant** — set `MQTT_BROKER` to HA's Mosquitto IP
- **+ Marchog** — set `MQTT_BROKER` + `MARCHOG_ENABLED=true`
