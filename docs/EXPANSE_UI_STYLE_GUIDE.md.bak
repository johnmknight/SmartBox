# The Expanse — UI Style Guide for Implementation
### Reference Document for MarchogSystemsOps Themed Interfaces

> **Scope**: Ship cockpit screens, space tracking displays, onscreen keyboards, kiosk/touch interfaces
> **Excluded**: Holographic/volumetric displays, hand terminal/phone devices
> **Sources**: Rhys Yorke (Motion Graphics, Seasons 3 & 5), Timothy Peel (Season 1, Junction Box), HUDS+GUIS, Fuzzy Math analysis

---

## 1. Design Philosophy

The Expanse UI is **functional first, beautiful second**. Every element serves a purpose — there is no decoration for decoration's sake.

> *"Nothing was meant to be superfluous or just there for visual interest. Everything was a part of that UI for purpose."*
> — Rhys Yorke, Motion Graphics Designer

### Key Principles

- **Operator-first**: Built for crew under duress, not consumers browsing. Hierarchy must be instantly readable.
- **Front-end / back-end hybrid**: Command-line terminal text is visible alongside polished controls. This "under the hood" quality gives the Rocinante its personality.
- **NASA-informed hierarchy**: The team consulted with a NASA astronaut on information priority — what matters most when inches of steel separate you from vacuum.
- **Military design discipline**: Clarity under stress, fast decision-making, minimal cognitive load.
- **Practical screen sizes**: Designers worked at actual on-set monitor dimensions, not idealized desktop mockups.

---

## 2. Faction Color Systems

The show uses color as **instant faction identification** — the viewer knows which ship they're on within a single frame.

### 2A. MCRN / Rocinante (Mars) — PRIMARY REFERENCE

![Rocinante UI](https://www.artstation.com/artwork/q9Am1L)
*See: [Rhys Yorke — Rocinante UI on ArtStation](https://www.artstation.com/artwork/q9Am1L)*

| Role | Color | Hex (approx) | Usage |
|------|-------|--------------|-------|
| Primary | Red | `#CC0000` – `#FF2200` | Borders, active controls, primary text |
| Nominal | Green | `#00CC44` | Systems OK, confirmed states |
| Warning | Yellow/Amber | `#FFAA00` | Alerts, attention-needed, docking status |
| Inactive/NA | Dim Red | `#441111` (low opacity) | Disabled controls, not-applicable items |
| Background | Near-black | `#0A0A0A` – `#111111` | Screen base |
| Text (primary) | White/Light gray | `#CCCCCC` – `#FFFFFF` | Readouts, labels |
| Text (secondary) | Dim red/pink | `#AA4444` | Subtitles, secondary info |

**Key insight**: When the entire palette is red, hierarchy is maintained through **opacity, size, and shape** — not just color. Fire controls that don't apply are dimmed to near-invisible rather than shown as red "N/A".

**Earth warnings on Mars ships appear in BLUE** — the enemy faction color becomes the threat color.

### 2B. UNN / Agatha King (Earth)

![Agatha King UI](https://rhysyorke.com/projects/g2J64x)
*See: [Rhys Yorke — Agatha King UI](https://rhysyorke.com/projects/g2J64x)*

| Role | Color | Hex (approx) | Usage |
|------|-------|--------------|-------|
| Primary | Blue | `#2266CC` – `#4488FF` | Borders, active panels |
| Accent | Orange | `#FF8800` | Draws eye, complements blue |
| Nominal | Green | `#22CC66` | Systems OK |
| Alert | Yellow | `#FFCC00` | Warnings, with yellow borders to differentiate from standard |
| Critical | Red | `#FF2200` | Errors, damage |
| Background | Dark blue-black | `#080C14` | Screen base |
| Text | White/Light blue | `#CCDDFF` | Readouts |

**Design influence**: WWII naval battleship control panels. Institutional, utilitarian, slightly behind Mars in "style" — intentionally less polished.

### 2C. OPA / Belter

| Role | Color | Hex (approx) | Usage |
|------|-------|--------------|-------|
| Primary | Amber/Orange | `#CC8800` – `#FF9900` | Primary UI elements |
| Accent | Brown/Rust | `#664422` | Secondary panels |
| Background | Dark brown-black | `#0C0A06` | Screen base |
| Text | Warm white/cream | `#DDCC99` | Readouts |

**Design influence**: Atari-era aesthetics. Retro, industrial, scrappy. Cobbled-together technology from multiple sources.

---

## 3. Typography

### Primary Font: Modified DIN Pro

The show uses a **modified version of DIN Pro** — a German industrial standard typeface. Geometric, highly legible, functional.

- **Fan recreation**: "Protomolecule" font — [GitHub: ThinkDualBrain/Protomolecule](https://github.com/ThinkDualBrain/Protomolecule)
- **Free alternative**: DIN family fonts, or Overpass / Share Tech / Barlow (similar geometric sans)

### Typography Rules

| Element | Style | Notes |
|---------|-------|-------|
| Labels & headers | ALL CAPS, wide letter-spacing | `letter-spacing: 0.1em` to `0.2em` |
| System readouts | Monospaced / terminal | Gives the "under the hood" command-line feel |
| Values (numbers) | Tabular figures, large weight | Numbers must be instantly readable under stress |
| Alerts | Large, bold, ALL CAPS | But NOT giant screen-filling boxes — the showrunner specifically rejected that trope |
| Status text | Sentence case or lowercase | Lower hierarchy, softer |

### Terminal / Command-Line Mix

A distinctive trait: **polished front-end controls sit alongside raw terminal output**. Log data, system messages, and diagnostic text scroll in monospaced type while the operator interacts with graphical controls. This creates the "crew interface" personality.

```
Implementation note:
- Use a split-panel approach: graphical controls on one side, scrolling terminal log on the other
- Terminal text should have slight dim opacity (~0.7) compared to primary controls
- Prefix system messages with timestamps: [14:23:07] REACTOR NOMINAL
```

---

## 4. Screen Layout Patterns

### 4A. Cockpit Screens (Curved Multi-Panel)

![Expanse Cockpit Screens](https://www.hudsandguis.com/home/2021/theexpanse)
*See: [HUDS+GUIS — The Expanse UI Design (full image gallery)](https://www.hudsandguis.com/home/2021/theexpanse)*

**Structure**: Screens wrap around operator stations. Each screen has a dedicated function.

```
┌──────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  NAVIGATION │  │   WEAPONS   │  │   COMMS      │      │
│  │             │  │             │  │              │      │
│  │  map/track  │  │  fire ctrl  │  │  channels    │      │
│  │  + orbit    │  │  + status   │  │  + messages  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
│  ┌───────────────────────┐  ┌──────────────────────┐     │
│  │    SHIP SYSTEMS       │  │   TERMINAL LOG       │     │
│  │  reactor / life sup   │  │  [scrolling text]    │     │
│  └───────────────────────┘  └──────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

**Panel characteristics**:
- Thin border lines (1–2px) in faction primary color
- Darker background inside panels than screen background (layered depth)
- Panel headers: ALL CAPS, small font, often with a thin rule underneath
- Content area: generous padding, never cramped
- Status bars along bottom edges of panels

### 4B. Tracking / Navigation Displays

*See: [Fuzzy Math — Sci-Fi UI Analysis of The Expanse](https://fuzzymath.com/blog/sci-fi-ui-what-three-spaceships-can-teach-us-about-the-future-of-user-interfaces/)*

Key tracking display elements:
- **Orbit lines**: Thin, low-opacity arcs showing object trajectories
- **Grid overlay**: Faint reference grid for distance estimation
- **Object markers**: Small geometric shapes (diamonds, circles) with text labels offset
- **Velocity vectors**: Lines extending from objects showing direction and speed
- **Distance readouts**: Numeric labels near objects, updating in real-time
- **Threat assessment**: Color-coded (green=friendly, red=hostile, yellow=unknown)

```
Implementation pattern:
- Dark background with very faint grid (#111111 lines on #0A0A0A)
- Orbit paths: 1px lines, ~20% opacity of faction primary
- Active targets: bright markers with pulsing or blinking edge
- Selected target: highlighted border, expanded info panel
- Scale indicator in corner
```

### 4C. Kiosk / Touch Interfaces

![Expanse Touch Screens](https://www.hudsandguis.com/home/2021/theexpanse)
*See: HUDS+GUIS gallery — touch screens and kiosks section*

- Large touch targets (designed for use with **heavy industrial gloves**)
- Simple, high-contrast layouts
- **Personality varies by location**: Ceres station kiosks feel different from Rocinante bridge controls
- Physical buttons mixed with touch — the show acknowledges tactile feedback matters

### 4D. Onscreen Keyboards

- **Large key targets** — minimum 48px equivalent
- **High contrast**: bright key borders on dark background
- **Minimal key set**: contextual keyboards show only what's needed
- **Visual feedback on press**: key brightens or inverts momentarily
- **Faction-colored accents**: key borders and highlights match the ship's palette

---

## 5. UI Component Patterns

### Borders & Containers

```css
/* Expanse-style panel border */
.expanse-panel {
  border: 1px solid rgba(204, 0, 0, 0.6);    /* faction primary, semi-transparent */
  background: rgba(10, 10, 10, 0.85);
  padding: 12px 16px;
}

.expanse-panel-header {
  font-family: 'DIN Pro', 'Overpass', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-size: 11px;
  color: rgba(204, 0, 0, 0.7);
  border-bottom: 1px solid rgba(204, 0, 0, 0.3);
  padding-bottom: 6px;
  margin-bottom: 10px;
}
```

### Status Indicators

```
● NOMINAL     — green dot + text
● CAUTION     — amber dot + text
● ALERT       — red dot + pulsing
○ OFFLINE     — hollow circle, dim text
◐ STANDBY     — half-fill, faction primary
```

### Buttons / Controls

- **Bordered rectangles**, not filled
- Border color = faction primary at ~60% opacity
- **Hover/Active**: border brightens to 100%, faint fill appears
- **Disabled**: border drops to ~20% opacity, text dims
- **No rounded corners** — sharp rectangles throughout (military/industrial)
- **No drop shadows** — flat, functional

```css
.expanse-button {
  border: 1px solid rgba(204, 0, 0, 0.5);
  background: transparent;
  color: #CCCCCC;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-family: 'DIN Pro', monospace;
  padding: 8px 20px;
  cursor: pointer;
}

.expanse-button:hover {
  border-color: #FF2200;
  background: rgba(204, 0, 0, 0.1);
  color: #FFFFFF;
}

.expanse-button:active {
  background: rgba(204, 0, 0, 0.25);
}

.expanse-button:disabled {
  border-color: rgba(204, 0, 0, 0.15);
  color: #444444;
}
```

### Data Tables

- **Thin horizontal rules** between rows
- **No vertical lines** — whitespace separates columns
- **Header row**: ALL CAPS, faction color, slightly smaller than content
- **Alternating row opacity**: subtle, not heavy striping
- **Active row**: left-edge highlight in faction primary

### Alert Banners

- **Yellow border** differentiates warnings from standard red controls (Rocinante pattern)
- **Large typography** for alert text but proportionate — not screen-filling
- Alerts appear in a **consistent location** (typically top of screen)
- **Dismissible** with clear action

---

## 6. Animation & Motion

### Principles
- **Functional transitions only** — no gratuitous animation
- **Data-driven motion**: numbers count up/down, progress bars fill, positions update
- **Subtle blinking** for attention states (not aggressive strobe)
- **Scan lines** on older/belter displays for retro character
- **Screen boot sequences**: text scrolling, system checks — the terminal aesthetic

### Timing
- **State changes**: 150–250ms transitions
- **Blinking indicators**: 800ms–1.2s cycle
- **Scroll speed**: terminal text at readable pace, not cinematic rush
- **Boot sequence**: can be drawn out for dramatic effect

---

## 7. Implementation Recommendations for MarchogSystemsOps

### Which Faction to Base On

| Use Case | Recommended Faction | Reasoning |
|----------|-------------------|-----------|
| Primary dashboard | MCRN (Red) | Already aligns with Marchog's existing red/black aesthetic |
| Tracking screens | UNN (Blue) | Blue reads as "operational/scanning" — Earth's military tracking UI is purpose-built |
| Belter/Industrial | OPA (Amber) | Good for sensor readouts, environmental data, workshop context |
| Mixed/Custom | Hybrid | Pick MCRN as base, use UNN blue for tracking elements |

### Font Stack

```css
font-family: 'Protomolecule', 'DIN Pro', 'Overpass', 'Barlow', sans-serif;

/* Terminal / readout text */
font-family: 'Space Mono', 'IBM Plex Mono', 'Fira Mono', monospace;
```

### CSS Custom Properties

```css
:root {
  /* MCRN / Mars Palette */
  --ex-primary: #CC0000;
  --ex-primary-bright: #FF2200;
  --ex-primary-dim: #441111;
  --ex-nominal: #00CC44;
  --ex-warning: #FFAA00;
  --ex-critical: #FF0000;
  --ex-background: #0A0A0A;
  --ex-panel-bg: #111111;
  --ex-text: #CCCCCC;
  --ex-text-bright: #FFFFFF;
  --ex-text-dim: #666666;
  --ex-border: rgba(204, 0, 0, 0.5);
  --ex-border-bright: rgba(255, 34, 0, 0.9);
}
```

---

## 8. Visual Reference Links

| Source | URL | Content |
|--------|-----|---------|
| HUDS+GUIS — The Expanse UI | [hudsandguis.com](https://www.hudsandguis.com/home/2021/theexpanse) | Comprehensive gallery: cockpit, kiosk, keyboard, all factions |
| Rhys Yorke — Rocinante UI | [artstation.com](https://www.artstation.com/artwork/q9Am1L) | Designer's portfolio: Roci screen designs, palette, layout |
| Rhys Yorke — Agatha King UI | [rhysyorke.com](https://rhysyorke.com/projects/g2J64x) | UNN blue/orange palette, WWII naval influence |
| Fuzzy Math — 3 Ships UI Analysis | [fuzzymath.com](https://fuzzymath.com/blog/sci-fi-ui-what-three-spaceships-can-teach-us-about-the-future-of-user-interfaces/) | Detailed UX analysis: Roci, Agatha King, Razorback |
| Pushing Pixels — Rhys Yorke Interview | [pushing-pixels.org](https://www.pushing-pixels.org/2021/09/04/the-art-and-craft-of-screen-graphics-interview-with-rhys-yorke.html) | Design process, faction color philosophy, NASA consultation |
| Pushing Pixels — Timothy Peel Interview | [pushing-pixels.org](https://www.pushing-pixels.org/2016/01/21/a-window-into-another-world-interview-with-timothy-peel.html) | Season 1 design: Ceres, medical, navigation interfaces |
| Protomolecule Font | [github.com](https://github.com/ThinkDualBrain/Protomolecule) | Fan recreation of show's modified DIN Pro |
| drainsmith Screenshot Archive | [imgur.com/a/ZokAK](https://imgur.com/a/ZokAK) | Massive screenshot dump: every screen type across all seasons |

---

*Document created: 2026-02-22 | SmartToolbox / MarchogSystemsOps subproject*