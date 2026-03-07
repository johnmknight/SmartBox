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
- [x] mode_weather.py (server-pushed, 3-col layout, Tabler icon spritesheet)
- [x] mode_battery.py
- [x] red_alert.py (Marchog interrupt)
- [x] lockdown.py (Marchog interrupt)
- [x] self_destruct.py (Marchog countdown)
- [x] Weather icon pipeline (build_weather_sprites.py → BMP spritesheet)
- [x] Per-box event commands (event_red_alert etc via command topic)
- [x] Server testing page (/testing) — event triggers, mode switch, weather push
- [x] Dashboard nav (Dashboard | Testing tabs)
- [x] Red Alert — Wrath of Khan style (chevron brackets, converging scan line animation)
- [x] Self Destruct — header text scale=2
- [x] Fast render interval (80ms) during interrupts
- [x] Server scaffold (FastAPI + SQLite) + web dashboard (rack view, sort by rack/category)
- [x] Category management API + seeded category list (18 categories with colors)
- [x] Rack manager UI (racks.html) — create/assign boxes, graphical rack view
- [x] Label generator (labels.html) — Plain/NASA/Hazard/Cargo templates, 3"×2" PNG export
- [x] NASA label — large meatball (84px), tall info-band (96px), stacked box-id + cat-badge
- [x] QR code fix — all boxes encode full URL (http://host/box/{id}), not bare box_id
- [x] /box/{id} mobile page — full NASA theme (stripe, meatball, Barlow Condensed name, orange CTA)
- [x] /box/{id} — battery badge hidden for passive boxes
- [x] Category badge font doubled on all label templates (Plain, NASA, Cargo)
- [x] Passive box treatment — battery bar + smart buttons hidden in dashboard and detail page
- [x] box_detail.py — category badge font doubled on mobile detail page

### NEXT UP 🔜
- [ ] Flash firmware to first Feather and test boot sequence
- [ ] Calibrate proximity_threshold with VCNL4020 mounted
- [ ] Test USB connect/disconnect state transitions
- [ ] Test button navigation between modes
- [ ] MQTT broker (embedded Mosquitto)
- [ ] Weather relay (HA or OpenWeatherMap)
- [ ] HA Discovery publisher
- [ ] Marchog integration bridge
- [ ] /box/{id} — inventory display (read-only view of saved manifest)
- [ ] Label generator — Hazard template category badge (no badge currently)
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
