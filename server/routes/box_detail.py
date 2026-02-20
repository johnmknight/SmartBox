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

    photo_html = f'<img id="photo" src="/api/boxes/{box_id}/photo?t=0" alt="Interior" onerror="this.style.display=\'none\';document.getElementById(\'no-photo\').style.display=\'flex\'">' if has_photo else ""
    no_photo_display = "none" if has_photo else "flex"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>{name} — SmartToolbox</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #080c10; color: #e0e8f0; font-family: 'Courier New', monospace;
         max-width: 480px; margin: 0 auto; padding: 16px; }}

  .header {{ border-bottom: 1px solid #00FF80; padding-bottom: 12px; margin-bottom: 16px; }}
  .box-id {{ color: #555; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; }}
  .box-name {{ font-size: 22px; color: #fff; font-weight: bold; margin: 4px 0; }}
  .category {{ font-size: 14px; color: #00d4ff; letter-spacing: 1px; }}

  .badges {{ display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }}
  .badge {{ padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;
            border: 1px solid; letter-spacing: 1px; }}

  .section {{ margin-bottom: 20px; }}
  .section-title {{ font-size: 11px; color: #555; letter-spacing: 2px; text-transform: uppercase;
                    margin-bottom: 8px; border-bottom: 1px solid #1a2030; padding-bottom: 4px; }}

  .photo-wrap {{ position: relative; width: 100%; aspect-ratio: 4/3; background: #0d1520;
                 border: 1px solid #1a2030; border-radius: 6px; overflow: hidden; cursor: pointer; }}
  .photo-wrap img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .no-photo {{ position: absolute; inset: 0; display: {no_photo_display}; flex-direction: column;
               align-items: center; justify-content: center; color: #333; gap: 8px; }}
  .no-photo svg {{ opacity: 0.3; }}
  .no-photo span {{ font-size: 12px; color: #444; }}
  .photo-hint {{ font-size: 11px; color: #333; text-align: center; margin-top: 6px; }}

  #file-input {{ display: none; }}

  textarea {{ width: 100%; min-height: 160px; background: #0d1520; border: 1px solid #1a2030;
              color: #e0e8f0; font-family: 'Courier New', monospace; font-size: 14px;
              padding: 10px; border-radius: 6px; resize: vertical; line-height: 1.6; }}
  textarea:focus {{ outline: none; border-color: #00d4ff; }}

  .btn {{ display: block; width: 100%; padding: 12px; background: #00d4ff; color: #000;
          font-family: 'Courier New', monospace; font-size: 14px; font-weight: bold;
          letter-spacing: 2px; border: none; border-radius: 6px; cursor: pointer;
          text-transform: uppercase; }}
  .btn:active {{ background: #00a0cc; }}
  .btn-success {{ background: #00FF80; }}

  .toast {{ position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
            background: #00FF80; color: #000; padding: 8px 20px; border-radius: 20px;
            font-size: 13px; font-weight: bold; opacity: 0; transition: opacity 0.3s;
            pointer-events: none; z-index: 100; }}
  .toast.show {{ opacity: 1; }}

  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .info-cell {{ background: #0d1520; border: 1px solid #1a2030; border-radius: 6px;
                padding: 8px 12px; }}
  .info-cell .lbl {{ font-size: 10px; color: #555; letter-spacing: 1px; text-transform: uppercase; }}
  .info-cell .val {{ font-size: 16px; font-weight: bold; margin-top: 2px; }}
</style>
</head>
<body>

<div class="header">
  <a href="/" style="display:inline-flex;align-items:center;gap:6px;color:#00d4ff;font-size:11px;letter-spacing:2px;text-decoration:none;margin-bottom:10px;opacity:0.7;">
    &#x2190; RACK
  </a>
  <div class="box-id">{box_id}</div>
  <div class="box-name">{name}</div>
  <div class="category">{category}</div>
  <div class="badges">
    <span class="badge" style="color:{state_color};border-color:{state_color};">{state}</span>
    <span class="badge" style="color:{bat_color};border-color:{bat_color};">BAT {bat_str}</span>
  </div>
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
  <div class="section-title">Inventory</div>
  <textarea id="inventory" placeholder="One item per line&#10;e.g.&#10;Phillips screwdriver #2&#10;Needle nose pliers&#10;Wire stripper">{inventory}</textarea>
</div>

<button class="btn" id="save-btn" onclick="saveInventory()">Save Inventory</button>

<div class="section">
  <div class="section-title">Event Log</div>
  <div id="event-log" style="display:flex;flex-direction:column;gap:6px;max-height:260px;overflow-y:auto;"></div>
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
      return `<div style="background:#0d1520;border:1px solid #1a2030;border-radius:6px;padding:8px 12px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
          <span style="font-size:11px;color:#00d4ff;letter-spacing:1px;">${{e.event_type.toUpperCase()}}</span>
          <span style="font-size:10px;color:#444;">${{t}}</span>
        </div>
        <div style="font-size:11px;color:#667788;">${{JSON.stringify(e.payload).slice(0,80)}}</div>
      </div>`;
    }}).join('');
  }} catch(e) {{}}
}}

loadEvents();
</script>
</body>
</html>"""
    return HTMLResponse(html)
