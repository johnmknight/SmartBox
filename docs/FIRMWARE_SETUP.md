# SmartToolbox — Firmware Setup Guide

**Hardware:** Adafruit ESP32-S3 Reverse TFT Feather  
**Firmware:** CircuitPython 10.1.1  
**Last updated:** 2025

---

## Hardware Overview

| Component | Part | Notes |
|---|---|---|
| MCU | Adafruit ESP32-S3 Reverse TFT Feather | Built-in 240×135 TFT, NeoPixel, 2 buttons |
| Proximity | VCNL4020 | I2C addr 0x13 — dock detection |
| Battery monitor | MAX17048 | I2C addr 0x36 — see Known Issues |
| Connection | USB-C | Home/dock signal + power |

---

## Step 1 — Flash CircuitPython

1. Download **CircuitPython 10.1.1** for the ESP32-S3 Reverse TFT Feather:  
   https://circuitpython.org/board/adafruit_feather_esp32s3_reverse_tft/

2. Hold the **BOOT** button, tap **RESET**, release BOOT — drive mounts as `ESP32S3BOOT`.

3. Copy the `.uf2` file to the drive. It reboots automatically as `CIRCUITPY`.

---

## Step 2 — Install CircuitPython Libraries

Copy these folders/files from the [CircuitPython 10.x Bundle](https://circuitpython.org/libraries) into `CIRCUITPY/lib/`:


| Library | Source |
|---|---|
| `adafruit_vcnl4020` | Bundle |
| `adafruit_max1704x` | Bundle |
| `adafruit_display_text` | Bundle |
| `adafruit_st7789` | Bundle |
| `adafruit_bitmap_font` | Bundle |
| `adafruit_imageload` | Bundle |
| `adafruit_minimqtt` | Bundle |
| `adafruit_ntp` | Bundle |
| `neopixel` | Bundle |

> **Tip:** Use [circup](https://github.com/adafruit/circup) to install/update libraries automatically:  
> `pip install circup && circup install --auto`

---

## Step 3 — Copy Firmware Files

Copy the entire contents of `firmware/` to the root of `CIRCUITPY/`:

```
CIRCUITPY/
├── code.py
├── config.json          ← edit this first (see Step 4)
├── display.py
├── sensor.py
├── power.py
├── state_machine.py
├── mqtt_client.py
├── settings.py
├── weather_icons.bmp
├── modes/
│   ├── mode_toolbox.py
│   ├── mode_clock.py
│   ├── mode_weather.py
│   ├── mode_battery.py
│   └── interrupts/
│       ├── red_alert.py
│       ├── lockdown.py
│       └── self_destruct.py
└── lib/                 ← libraries from Step 2
```


---

## Step 4 — Edit config.json

Edit `config.json` before copying to the Feather. Every box gets its own file.

```json
{
  "box_id": "box-01",          // unique ID — must match server DB
  "rack_id": "rack-01",        // rack assignment
  "display_name": "Box 1",     // human-readable name shown on TFT

  "wifi_ssid": "YOUR_SSID",
  "wifi_pass": "YOUR_PASSWORD",

  "server_url": "http://192.168.4.47:8091",

  "use_mqtt": true,
  "mqtt_broker": "192.168.4.47",
  "mqtt_port": 1883,
  "mqtt_user": "",
  "mqtt_pass": "",

  "use_marchog": false,

  "proximity_threshold": 50,   // ← calibrate per box (see Step 6)
  "proximity_samples": 5,

  "timezone_offset": -4,       // UTC offset (EDT = -4, EST = -5)
  "display_brightness": 1.0,
  "weather_unit": "F",
  "debug": true
}
```

> **Note:** `box_id` must exactly match the ID created in the server dashboard.  
> Create the box at `http://192.168.4.47:8091` before first boot.

---

## Step 5 — First Boot Sequence

1. Plug in USB-C. The Feather boots and runs `code.py` automatically.
2. Watch the serial console (Mu editor, Thonny, or `screen /dev/ttyACM0 115200`).
3. Expected boot log:
```
[settings] Loaded config for box-01
[power] USB connected — state: DOCKED
[sensor] VCNL4020 ready at 0x13
[state] DOCKED
[wifi] Connected to DSN1 — IP 192.168.4.x
[mqtt] Connected to 192.168.4.47:1883
[mqtt] Published boot message
[display] TFT ready
[mode] Switching to toolbox mode
```

4. TFT should show the toolbox status screen. NeoPixel glows green (DOCKED).


---

## Step 6 — Calibrate Proximity Threshold

The VCNL4020 returns raw counts (not mm). The threshold must be set per-box because mounting geometry and box material affect readings.

**Procedure:**

1. Mount the Feather in its final position inside the box lid or rack.
2. Open the serial console.
3. Temporarily set `debug: true` in `config.json`.
4. Watch the proximity readings print each loop cycle.
5. Note the count value when the box is **docked** (seated in rack, USB connected).
6. Note the count value when the box is **away** (removed from rack).
7. Set `proximity_threshold` halfway between the two values.

**Example:**
```
Docked reading:  ~320 counts
Away reading:    ~15 counts
Good threshold:  ~50  (default)
```

> **Rule:** Raw counts increase as the target gets closer.  
> Threshold = box is "docked" if reading > threshold.

---

## Step 7 — State Machine Verification

Test each transition manually:

| Action | Expected State | NeoPixel | TFT Mode |
|---|---|---|---|
| USB-C connected, in rack | DOCKED | Green | Toolbox |
| USB-C disconnected, in rack | DOCKING → DOCKED | Cyan → Green | Toolbox |
| Removed from rack | AWAY | Amber | Clock |
| Set down on surface (prox high, no USB) | SET_DOWN | Yellow | Clock |
| Returning to rack | DOCKING | Cyan | — |

> **Settle times:** DOCKING=0.5s, all others=2.0s — prevents flicker on brief contact.

---

## Step 8 — Button Navigation

| Button | Action |
|---|---|
| **BTN0** (left, GPIO 0) | Previous mode |
| **BTN1** (right, GPIO 1) | Next mode |

Mode cycle: `toolbox → clock → weather → battery → (repeat)`

Marchog interrupt modes (red_alert, lockdown, self_destruct) override the normal cycle and return automatically.

---

## Known Issues

### MAX17048 Battery Monitor — I2C Drop After Display Init

**Symptom:** `I2C scan returns []` after `displayio.release_displays()`.  
**Root cause:** `displayio.release_displays()` de-powers `TFT_I2C_POWER` pin, killing the I2C bus.  
**Fix applied in `display.py`:** Re-enables `TFT_I2C_POWER` after release + 100ms settle delay.  
**Status:** Fix applied but unconfirmed on replacement hardware.

**On first boot with new board:**
```python
# Run this from REPL before loading firmware to confirm MAX17048 is present:
import busio, board
i2c = busio.I2C(board.SCL, board.SDA)
i2c.try_lock()
print([hex(x) for x in i2c.scan()])
# Expected: ['0x13', '0x36']  (VCNL4020 + MAX17048)
```
If `0x36` is missing, the I2C power fix needs adjustment before enabling the full firmware.

---

### supervisor.runtime.usb_connected Reliability

`supervisor.runtime.usb_connected` can return `True` briefly during USB enumeration even when not fully connected. The state machine uses a 0.5s settle time for DOCKING to filter noise. If transitions are erratic, increase `DOCKING_SETTLE` in `state_machine.py`.

---

### NTP Sync Requires WiFi

Clock mode displays the last synced time. If WiFi is unavailable at boot, NTP sync is skipped silently and the clock shows `00:00:00` until WiFi connects. This is expected behavior — no fix needed.

---

### proximity_threshold Uses Raw Counts, Not mm

The value in `config.json` is a raw VCNL4020 proximity count, not a physical distance. Must be calibrated per-box. See Step 6.

---

## MQTT Topics

All topics follow the pattern `smarttoolbox/{box_id}/{type}`:

| Topic | Direction | Payload |
|---|---|---|
| `smarttoolbox/{id}/state` | Feather → Server | `{state, rack_id, display_name}` |
| `smarttoolbox/{id}/battery` | Feather → Server | `{pct, voltage, charging}` |
| `smarttoolbox/{id}/boot` | Feather → Server | `{version, rack_id, display_name}` |
| `smarttoolbox/{id}/command` | Server → Feather | `{action, ...}` |
| `smarttoolbox/{id}/weather` | Server → Feather | weather payload |

**Available commands:**

| action | Effect |
|---|---|
| `identify` | Flash NeoPixel to locate box |
| `set_category` | Update category label on TFT |
| `set_mode` | Force switch to specific mode |
| `reboot` | Soft reboot via supervisor |
| `event_red_alert` | Trigger Red Alert interrupt |
| `event_lockdown` | Trigger Lockdown interrupt |
| `event_self_destruct` | Trigger Self Destruct countdown |
| `event_all_clear` | Clear active interrupt |
