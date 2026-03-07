# server/routes/box_detail.py
import os, aiosqlite
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from server.database import get_db, DB_PATH

router = APIRouter()

PHOTOS_DIR = Path("data/photos")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

class InventoryUpdate(BaseModel):
    inventory: str

# ── Inventory ──────────────────────────────────────────────────────────────

@router.get("/api/boxes/{box_id}/inventory")
async def get_inventory(box_id: str, db=Depends(get_db)):
    async with db.execute("SELECT inventory FROM boxes WHERE box_id=?", (box_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Box not found")
    return {"box_id": box_id, "inventory": row["inventory"] or ""}

@router.put("/api/boxes/{box_id}/inventory")
async def set_inventory(box_id: str, body: InventoryUpdate, db=Depends(get_db)):
    await db.execute("UPDATE boxes SET inventory=? WHERE box_id=?", (body.inventory, box_id))
    await db.commit()
    return {"ok": True}

# ── Photo ──────────────────────────────────────────────────────────────────

@router.post("/api/boxes/{box_id}/photo")
async def upload_photo(box_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    ext = Path(file.filename).suffix.lower() or ".jpg"
    dest = PHOTOS_DIR / f"{box_id}{ext}"
    data = await file.read()
    dest.write_bytes(data)
    await db.execute("UPDATE boxes SET photo_path=? WHERE box_id=?", (str(dest), box_id))
    await db.commit()
    return {"ok": True, "path": str(dest)}

@router.get("/api/boxes/{box_id}/photo")
async def get_photo(box_id: str, db=Depends(get_db)):
    async with db.execute("SELECT photo_path FROM boxes WHERE box_id=?", (box_id,)) as cur:
        row = await cur.fetchone()
    if not row or not row["photo_path"] or not Path(row["photo_path"]).exists():
        raise HTTPException(404, "No photo")
    return FileResponse(row["photo_path"])

# ── Mobile page ────────────────────────────────────────────────────────────

@router.get("/box/{box_id}", response_class=HTMLResponse)
async def box_page(box_id: str, db=Depends(get_db)):
    async with db.execute("SELECT * FROM boxes WHERE box_id=?", (box_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        return HTMLResponse("<h1>Box not found</h1>", status_code=404)

    box = dict(row)
    has_photo = bool(box.get("photo_path") and Path(box["photo_path"]).exists())
    category  = box.get("category") or "Unassigned"
    state     = box.get("state") or "UNKNOWN"
    pct       = box.get("battery_pct", -1)
    inventory = box.get("inventory") or ""
    name      = box.get("display_name") or box_id

    state_color = {"DOCKED":"#00FF80","AWAY":"#F59E0B","SET_DOWN":"#FFFF00","DOCKING":"#00D4FF"}.get(state,"#888888")
    bat_color   = "#FF4444" if pct < 20 else "#F59E0B" if pct < 50 else "#00FF80"
    bat_str     = f"{pct:.0f}%" if pct >= 0 else "---"
    bat_badge   = "" if state == "passive" else f'<span class="badge" style="color:{bat_color};border-color:{bat_color};">BAT {bat_str}</span>'

    photo_html = f'<img id="photo" src="/api/boxes/{box_id}/photo?t=0" alt="Interior" onerror="this.style.display=\'none\';document.getElementById(\'no-photo\').style.display=\'flex\'">' if has_photo else ""
    no_photo_display = "none" if has_photo else "flex"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>{name} — SmartToolbox</title>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #09111f; color: #c8d8e8;
          font-family: 'Share Tech Mono', 'Courier New', monospace;
          max-width: 480px; margin: 0 auto; min-height: 100vh; }}

  .stripe {{ height: 6px; background: #e36b00; width: 100%; }}
  .nasa-band {{
    background: #060b15; border-bottom: 1px solid #1e3a5f;
    padding: 12px 16px; display: flex; align-items: center; gap: 14px;
  }}
  .nasa-meatball {{ width: 56px; height: 56px; flex-shrink: 0; }}
  .nasa-band-text {{ flex: 1; }}
  .nasa-back {{ display: inline-flex; align-items: center; gap: 4px;
                color: #e36b00; font-size: 10px; letter-spacing: 2px;
                text-decoration: none; opacity: 0.8; margin-bottom: 4px; }}
  .box-id-mono {{ color: #00d4ff; font-size: 1rem; letter-spacing: 3px; }}
  .cat-badge {{
    display: inline-block; margin-top: 4px;
    font-size: 20px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    color: #e36b00; border: 1px solid #e36b00; padding: 2px 10px;
  }}
  .name-hero {{ background: #09111f; padding: 14px 16px 12px; border-bottom: 1px solid #1e3a5f; }}
  .box-name {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.8rem; font-weight: 900; color: #fff;
    text-transform: uppercase; letter-spacing: -1px; line-height: 1;
  }}
  .meta-row {{ display: flex; gap: 24px; margin-top: 8px; }}
  .meta-item {{ display: flex; flex-direction: column; }}
  .meta-key {{ font-size: 9px; font-weight: 700; text-transform: uppercase;
               letter-spacing: 2px; color: #334155; }}
  .meta-val {{ font-size: 13px; font-weight: 700; color: #00d4ff; letter-spacing: 1px; }}
  .bat-badge {{
    display: inline-block; margin-top: 8px;
    padding: 2px 10px; font-size: 11px; font-weight: bold;
    border: 1px solid; letter-spacing: 2px; text-transform: uppercase;
  }}

  .section {{ padding: 14px 16px; border-bottom: 1px solid #0e1d2e; }}
  .section-title {{ font-size: 9px; color: #334155; letter-spacing: 3px;
                    text-transform: uppercase; margin-bottom: 10px; }}
  .photo-wrap {{ position: relative; width: 100%; aspect-ratio: 4/3;
                 background: #060b15; border: 1px solid #1e3a5f;
                 overflow: hidden; cursor: pointer; }}
  .photo-wrap img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .no-photo {{ position: absolute; inset: 0; display: {no_photo_display}; flex-direction: column;
               align-items: center; justify-content: center; color: #1e3a5f; gap: 8px; }}
  .no-photo svg {{ opacity: 0.4; }}
  .no-photo span {{ font-size: 11px; color: #334155; letter-spacing: 2px; text-transform: uppercase; }}
  .photo-hint {{ font-size: 10px; color: #1e3a5f; text-align: center;
                 margin-top: 6px; letter-spacing: 1px; }}
  #file-input {{ display: none; }}
  textarea {{ width: 100%; min-height: 150px; background: #060b15; border: 1px solid #1e3a5f;
              color: #c8d8e8; font-family: 'Share Tech Mono', monospace;
              font-size: 13px; padding: 10px; resize: vertical; line-height: 1.7; }}
  textarea:focus {{ outline: none; border-color: #00d4ff; }}
  .btn {{ display: block; width: calc(100% - 32px); margin: 0 16px 16px;
          padding: 13px; background: #e36b00; color: #fff;
          font-family: 'Share Tech Mono', monospace; font-size: 13px; font-weight: bold;
          letter-spacing: 3px; border: none; cursor: pointer; text-transform: uppercase; }}
  .btn:active {{ background: #c05a00; }}
  .btn-success {{ background: #00FF80 !important; color: #000; }}
  .event-item {{ background: #060b15; border: 1px solid #0e1d2e; padding: 8px 12px; margin-bottom: 6px; }}
  .event-type {{ font-size: 10px; color: #00d4ff; letter-spacing: 2px; }}
  .event-time {{ font-size: 10px; color: #334155; }}
  .event-payload {{ font-size: 11px; color: #334155; margin-top: 2px; }}
  .toast {{ position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
            background: #e36b00; color: #fff; padding: 8px 20px;
            font-size: 12px; font-weight: bold; letter-spacing: 2px;
            opacity: 0; transition: opacity 0.3s; pointer-events: none; z-index: 100; }}
  .toast.show {{ opacity: 1; }}
  .nasa-footer {{ padding: 10px 16px; display: flex; justify-content: space-between;
                  font-size: 9px; color: #1e3a5f; letter-spacing: 2px; text-transform: uppercase; }}
</style>
</head>
<body>

<div class="stripe"></div>
<div class="nasa-band">
  <img class="nasa-meatball" src="/client/assets/nasa-meatball.svg" alt="NASA"
       onerror="this.style.display='none'">
  <div class="nasa-band-text">
    <a class="nasa-back" href="/">&#x2190; RACK</a><br>
    <span class="box-id-mono">{box_id}</span><br>
    <span class="cat-badge">{category}</span>
  </div>
</div>

<div class="name-hero">
  <div class="box-name">{name}</div>
  <div class="meta-row">
    <div class="meta-item">
      <span class="meta-key">Zone</span>
      <span class="meta-val">{box.get('zone') or '—'}</span>
    </div>
    <div class="meta-item">
      <span class="meta-key">Rack</span>
      <span class="meta-val">{box.get('rack_id') or '—'}</span>
    </div>
    <div class="meta-item">
      <span class="meta-key">Type</span>
      <span class="meta-val">{state.upper()}</span>
    </div>
  </div>
  {f'<span class="bat-badge" style="color:{bat_color};border-color:{bat_color};">BAT {bat_str}</span>' if state != "passive" else ''}
</div>

<div class="section">
  <div class="section-title">Interior Photo</div>
  <div class="photo-wrap" onclick="document.getElementById('file-input').click()">
    {photo_html}
    <div class="no-photo" id="no-photo">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <rect x="2" y="4" width="20" height="16" rx="2"/><circle cx="12" cy="12" r="4"/>
        <path d="M8 4l1.5-2h5L16 4"/>
      </svg>
      <span>Tap to add photo</span>
    </div>
  </div>
  <div class="photo-hint">Tap photo to replace</div>
  <input type="file" id="file-input" accept="image/*" capture="environment">
</div>

<div class="section">
  <div class="section-title">Inventory Manifest</div>
  <textarea id="inventory" placeholder="One item per line&#10;&#10;e.g.&#10;Phillips screwdriver #2&#10;Needle nose pliers&#10;Wire stripper">{inventory}</textarea>
</div>

<button class="btn" id="save-btn" onclick="saveInventory()">Save Manifest</button>

<div class="section">
  <div class="section-title">Event Log</div>
  <div id="event-log" style="display:flex;flex-direction:column;gap:6px;max-height:260px;overflow-y:auto;"></div>
</div>

<div class="nasa-footer">
  <span>SMARTTOOLBOX // {box_id}</span>
  <span>STB-MOBILE-V2</span>
</div>

<div class="toast" id="toast"></div>

<script>
const BOX_ID = "{box_id}";

// Photo upload
document.getElementById('file-input').addEventListener('change', async (e) => {{
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`/api/boxes/${{BOX_ID}}/photo`, {{ method: 'POST', body: fd }});
  if (r.ok) {{
    const img = document.getElementById('photo');
    const noPhoto = document.getElementById('no-photo');
    const ts = Date.now();
    if (img) {{
      img.src = `/api/boxes/${{BOX_ID}}/photo?t=${{ts}}`;
      img.style.display = 'block';
    }} else {{
      const wrap = document.querySelector('.photo-wrap');
      const newImg = document.createElement('img');
      newImg.id = 'photo';
      newImg.src = `/api/boxes/${{BOX_ID}}/photo?t=${{ts}}`;
      newImg.alt = 'Interior';
      wrap.insertBefore(newImg, wrap.firstChild);
    }}
    if (noPhoto) noPhoto.style.display = 'none';
    toast('Photo saved');
  }}
}});

// Inventory save
async function saveInventory() {{
  const text = document.getElementById('inventory').value;
  const btn = document.getElementById('save-btn');
  const r = await fetch(`/api/boxes/${{BOX_ID}}/inventory`, {{
    method: 'PUT',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{ inventory: text }})
  }});
  if (r.ok) {{
    btn.classList.add('btn-success');
    btn.textContent = 'SAVED ✓';
    setTimeout(() => {{ btn.classList.remove('btn-success'); btn.textContent = 'SAVE INVENTORY'; }}, 2000);
    toast('Inventory saved');
  }}
}}

function toast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}}

// Event log
async function loadEvents() {{
  try {{
    const r = await fetch(`/api/boxes/${{BOX_ID}}/events?limit=20`);
    if (!r.ok) return;
    const events = await r.json();
    const log = document.getElementById('event-log');
    if (!events.length) {{
      log.innerHTML = '<div style="font-size:12px;color:#444;padding:8px;">No events yet</div>';
      return;
    }}
    log.innerHTML = events.map(e => {{
      const t = new Date(e.ts).toLocaleTimeString([], {{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
      return `<div class="event-item">
        <div style="display:flex;justify-content:space-between;">
          <span class="event-type">${{e.event_type.toUpperCase()}}</span>
          <span class="event-time">${{t}}</span>
        </div>
        <div class="event-payload">${{JSON.stringify(e.payload).slice(0,80)}}</div>
      </div>`;
    }}).join('');
  }} catch(e) {{}}
}}

loadEvents();
</script>
</body>
</html>"""
    return HTMLResponse(html)
