# SmartToolbox Production Queue

## Active Sprint: Firmware Foundation

### DONE ✅
- [x] Project scaffold + directory structure
- [x] config.json + settings.py
- [x] sensor.py (VCNL4020)
- [x] power.py (USB detect + MAX17048)
- [x] state_machine.py (DOCKED/AWAY/SET_DOWN)
- [x] display.py (TFT + buttons + NeoPixel)
- [x] mqtt_client.py (pub/sub + reconnect)
- [x] code.py (main loop)
- [x] mode_toolbox.py
- [x] mode_clock.py (+ NTP sync)
- [x] mode_weather.py (server-pushed)
- [x] mode_battery.py
- [x] red_alert.py (Marchog interrupt)
- [x] lockdown.py (Marchog interrupt)
- [x] self_destruct.py (Marchog countdown)

### NEXT UP 🔜
- [ ] Flash firmware to first Feather and test boot sequence
- [ ] Calibrate proximity_threshold with VCNL4020 mounted
- [ ] Test USB connect/disconnect state transitions
- [ ] Test button navigation between modes
- [ ] Server scaffold (FastAPI + SQLite)
- [ ] MQTT broker (embedded Mosquitto)
- [ ] Web dashboard (rack view)
- [ ] Category management API + UI
- [ ] Weather relay (HA or OpenWeatherMap)
- [ ] HA Discovery publisher
- [ ] Marchog integration bridge
- [ ] .env.example + install.sh
- [ ] docs/FIRMWARE_SETUP.md

### BLOCKED ⏸
- [ ] MAX17048 battery monitor — possible hardware defect on current board
  - Root cause: `displayio.release_displays()` drops `TFT_I2C_POWER`, killing power to I2C bus + MAX17048
  - Fix applied: re-enable `TFT_I2C_POWER` in display.py after release, 100ms settle delay
  - Still failing — I2C scan returns [] even with pin manually driven HIGH from REPL
  - Likely hardware issue on this unit; new board on order
  - When new board arrives: run bare REPL scan first to confirm MAX17048 at 0x36 before loading firmware

### KNOWN ISSUES / TO VERIFY
- [ ] VCNL4020 I2C address conflict check (0x13) — no conflict since each box has its own Feather
- [ ] supervisor.runtime.usb_connected reliability on ESP32-S3
- [ ] NTP sync needs WiFi — verify fallback behavior when offline
- [ ] proximity_threshold in config.json uses raw counts not mm — needs bench calibration note in docs
