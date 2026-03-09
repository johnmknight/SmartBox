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
- [x] State machine transitions — DOCKING pixel color (cyan), per-state settle times (DOCKING=0.5s vs 2.0s for others), auto-mode-switch on DOCKED→toolbox / AWAY→clock
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
- [x] RFID/NFC sprint — NTAG215 provisioning system
  - database.py: last_rfid_accessed, rfid_provisioned, rfid_provisioned_at migration columns
  - box_detail.py: ?via=rfid, rfid-ping POST, Last NFC Tap + Last Seen in meta row, live state refresh via JS fetch
  - routes/rfid.py: /provision dashboard, /provision/{id}/write (NFC Tools primary flow), /provision/{id}/confirm
  - main.py: rfid router registered
  - index.html: NFC nav link added
  - rfid.py: NFC_HOST/NFC_PORT env vars, correct default 192.168.4.47
  - .env + .env.example: NFC_HOST=192.168.4.47, NFC_PORT=8091
  - Write page: Web NFC removed (Option C), NFC Tools is sole path, clipboard fallback, already-provisioned badge, confirm error recovery, 800ms next-box delay

### MOBILE UI — In Progress 📱
- [x] /m — Mobile fleet dashboard (box list, state-sorted, filter chips, live stats, 15s auto-refresh)
- [x] /box/{id} — Redesigned detail page (state as visual centerpiece with glow, battery bar, bottom nav)
- [x] mobile route registered in main.py, Mobile link added to desktop nav
- [x] anthropic>=0.25.0 added to requirements.txt, installed to system Python 3.12
- [x] ANTHROPIC_API_KEY added to .env and .env.example
- [x] server/routes/ai_scan.py: POST /box/{id}/ai-scan — Claude vision, [AI] prefix append, dedup, timestamp separator
- [x] box_detail.py: Scan Contents button, spinner, status text, [AI] badge on inventory items
- [x] main.py: ai_scan router registered
- [ ] PWA manifest + home screen icon (add to head on /m and /box/{id})
- [ ] Swipe-to-refresh on /m (touch event handler)
- [ ] Box detail — action sheet for MQTT commands (identify/reboot) via bottom nav
- [ ] Box detail — photo lightbox (tap to expand full-screen)
- [ ] Offline state: service worker caches last-known box data
- [ ] Flash firmware to first Feather and test boot sequence
- [ ] Calibrate proximity_threshold with VCNL4020 mounted
- [ ] Test USB connect/disconnect state transitions
- [ ] Test button navigation between modes
- [ ] MQTT broker (embedded Mosquitto)
- [ ] Weather relay (HA or OpenWeatherMap)
- [ ] HA Discovery publisher
- [ ] Marchog integration bridge
- [x] /box/{id} — inventory display (read-only manifest view with item count, Edit toggle, cancel)
- [x] Label generator — Hazard template category badge (black-on-yellow badge, wired to cat color system)
- [x] .env.example + install.sh (Python version check, venv, pip, .env copy, data/photos mkdir, Mosquitto check, DB init)
- [x] docs/FIRMWARE_SETUP.md (hardware, CircuitPython flash, library list, config.json reference, boot sequence, proximity calibration, state machine verification, button nav, known issues, MQTT topics)

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
