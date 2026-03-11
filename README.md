# SmartToolbox

ESP32-S3 Reverse TFT Feather firmware + server for intelligent tool storage tracking.

## Hardware (per box)
- Adafruit ESP32-S3 Reverse TFT Feather (#5691)
- Adafruit VCNL4020 Proximity + Light Sensor (#5860) via STEMMA QT
- LiPoly battery
- USB-C dock connector (rack-mounted)

## Live Deployment

Running on **appserv1** (Raspberry Pi, 192.168.4.148) via Docker.

| URL | Description |
|-----|-------------|
| `http://appserv1.local:8091` | Desktop dashboard |
| `http://appserv1.local:8091/m` | Mobile fleet view |
| `http://appserv1.local:8091/testing` | Event / mode testing |
| `http://appserv1.local:8091/provision` | NFC provisioning |
| `appserv1.local:1883` | MQTT broker (Mosquitto) |

DNS via Pi-hole on dev1 (192.168.4.49). `appserv1.local` resolves on all LAN devices.

## Quick Start — Local Dev

```bash
cp .env.example .env  # edit as needed
pip install -r requirements.txt
python server/main.py
```

## Docker Deploy (appserv1)

Images are built for ARM64 and pushed to `ghcr.io/johnmknight/smartlab-smarttoolbox`.
Deploy scripts are in `C:\Users\john_\dev\pi-deploy\`.

```bat
# Build + push ARM64 image
pi-deploy\deploy.bat

# SSH to appserv1 and pull + restart
ssh john@appserv1.local "cd ~/smartlab && docker compose pull && docker compose up -d"
```

**DB location on appserv1:** `~/smartlab/data/smarttoolbox/db/smarttoolbox.db`

To migrate DB from dev:
```powershell
docker stop smarttoolbox
scp smarttoolbox\data\smarttoolbox.db john@appserv1.local:~/smartlab/data/smarttoolbox/db/smarttoolbox.db
ssh john@appserv1.local "docker start smarttoolbox"
```

## Firmware Quick Start

1. Flash CircuitPython 10.x to the Feather
2. `circup install adafruit_minimqtt adafruit_vcnl4020 adafruit_max1704x adafruit_st7789 adafruit_display_text adafruit_ntp neopixel`
3. Edit `firmware/config.json` — set WiFi SSID/pass and `server_url: http://appserv1.local:8091`
4. Copy all `firmware/` files to the Feather's CIRCUITPY drive

See `docs/FIRMWARE_SETUP.md` for full calibration and troubleshooting guide.

## Deployment Scenarios
- **Standalone** — no MQTT config needed, embedded broker starts automatically
- **+ Home Assistant** — set `MQTT_BROKER` to HA's Mosquitto IP
- **+ Marchog** — set `MQTT_BROKER` + `MARCHOG_ENABLED=true`
