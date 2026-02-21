# SmartToolbox — Interrupt Event Design Notes

## Overview
Interrupt events override normal display modes on the TFT (240×135).
Triggered via Marchog broadcast topics or per-box command actions.
Three event types: Red Alert, Lockdown, Self Destruct.
Dismissed by All Clear.

## Current State (v1.0)

### Red Alert (`red_alert.py`)
- Pulsing red background (0xFF0000 / 0x220000 alternating)
- NeoPixel synced to pulse
- "RED ALERT" text centered (scale=3, white)
- Box display name below (scale=1)
- Pulse rate: 0.5s toggle

### Lockdown (`lockdown.py`)
- Static amber background (0x2A1A00)
- "LOCKDOWN" text centered (scale=3, amber)
- Box ID below (scale=2)
- "SECURE AND HOLD" subtitle (scale=1)
- No animation

### Self Destruct (`self_destruct.py`)
- Countdown timer (scale=5, center)
- Background color shifts: orange → red as time runs out
- Sub-10s: NeoPixel rapid strobe
- "SELF DESTRUCT" header (scale=1)
- Detonation flash sequence on completion
- **DESIGN NOTE: "SELF DESTRUCT" label text too small at scale=1. Increase to scale=2 minimum.**

---

## Planned Improvements

### Self Destruct — Text Size
- Increase "SELF DESTRUCT" header from scale=1 to scale=2
- Reposition to maintain visual balance with countdown digits
- Consider dropping box name to free vertical space

### Red Alert — Animation Rework
Current simple pulse is functional but not cinematic enough.
Target: Choose one primary animation style, keep NeoPixel sync.

#### Candidate Animation Styles

**1. Center Split (PREFERRED — user requested)**
Two red rectangles start touching at screen center.
They part/slide outward to screen edges, revealing "RED ALERT" on black.
Then snap back together. Repeat on loop.
- Implementation: Two TileGrids (left half, right half), adjust `.x` each frame
- Timing: ~1s full open, 0.3s hold, snap close, 0.3s hold, repeat
- NeoPixel: Bright when closed (red flash), dim when open
- Variation: Could wipe from center vertically instead of horizontally

**2. Horizontal Scan Wipe**
A narrow red bar (maybe 20px tall) sweeps top-to-bottom across screen.
Trail fades from bright red to dark red behind it.
"RED ALERT" text always visible.
- Implementation: Single tall TileGrid that moves `.y`, palette shift for trail
- Gives a radar/scanner feel
- Lower visual impact than center split

**3. Expanding Border**
Red border grows inward from screen edges toward center.
At full thickness, snaps back to thin border. Repeat.
"RED ALERT" text in center, always visible.
- Implementation: Draw concentric rectangles into bitmap, vary border width
- More subtle, control-panel aesthetic
- Could combine with text flash

**4. Alternating Hazard Stripes**
Diagonal red/black stripes that scroll continuously.
"RED ALERT" text overlaid on top.
- Implementation: Pre-rendered stripe bitmap, shift TileGrid `.x` to animate
- Busy look, may be hard to read text
- Better suited for "WARNING" than "RED ALERT"

**5. Vertical Blinds**
Red columns that open/close like window blinds.
Black gaps widen and narrow rhythmically.
- Implementation: Multiple narrow TileGrids
- Complex, many display objects may hurt perf on CircuitPython

**6. Text Glitch Flicker**
Red background with "RED ALERT" text that randomly:
- Shifts position by a few pixels
- Drops characters momentarily
- Inverts colors briefly
- Like a corrupted CRT signal
- Could combine with any background animation

#### Hardware Constraints
- CircuitPython `displayio`: bitmap-based, no GPU acceleration
- Render budget: ~50ms per frame is comfortable, 100ms+ causes visible lag
- TileGrid count: keep under 10-12 for smooth updates
- Palette swaps are free (no redraw needed)
- Bitmap pixel writes are slow for large areas
- Moving existing TileGrids (changing `.x`, `.y`) is fast

#### Recommendation
**Center Split** is the strongest candidate:
- Only 4 display objects needed (2 red panels + 2 text labels)
- TileGrid repositioning is fast on displayio
- High visual drama — feels like blast doors opening
- Clear Star Trek / sci-fi lineage
- Text reveal adds urgency (hidden → visible → hidden)
- NeoPixel sync is natural (flash on close, dim on open)

---

## MQTT Topics

### Marchog Broadcast (all boxes)
```
marchog/event/red-alert        {}
marchog/event/lockdown         {}
marchog/event/self-destruct    {"countdown": 30}
marchog/event/all-clear        {}
```

### Per-Box Command (single box)
```
smarttoolbox/{box_id}/command
  {"action": "event_red_alert"}
  {"action": "event_lockdown"}
  {"action": "event_self_destruct", "countdown": 30}
  {"action": "event_all_clear"}
```

## Testing
Server testing page at `/testing` provides:
- Box selector dropdown
- Event trigger buttons (Red Alert, Lockdown, Self Destruct + countdown, All Clear)
- Display mode switcher
- Weather data push form
- Identify + Reboot quick actions
- Command log
