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

@router.post("/api/boxes/{box_id}/photo")
async def upload_photo(box_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    ext = Path(file.filename).suffix.lower() or ".jpg"
    dest = PHOTOS_DIR / f"{box_id}{ext}"
    dest.write_bytes(await file.read())
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

@router.post("/box/{box_id}/rfid-ping")
async def rfid_ping(box_id: str, db=Depends(get_db)):
    async with db.execute("SELECT box_id FROM boxes WHERE box_id=?", (box_id,)) as cur:
        if not await cur.fetchone():
            raise HTTPException(404, "Box not found")
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await db.execute("UPDATE boxes SET last_rfid_accessed=? WHERE box_id=?", (ts, box_id))
    await db.commit()
    return {"ok": True, "last_rfid_accessed": ts}


@router.get("/box/{box_id}", response_class=HTMLResponse)
async def box_page(box_id: str, via: str = None, db=Depends(get_db)):
    async with db.execute("SELECT * FROM boxes WHERE box_id=?", (box_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        return HTMLResponse("<h1>Box not found</h1>", status_code=404)

    box = dict(row)
    name      = box.get("display_name") or box_id
    category  = box.get("category") or "Unassigned"
    state     = (box.get("state") or "UNKNOWN").upper()
    pct       = box.get("battery_pct", -1)
    inventory = box.get("inventory") or ""
    has_photo = bool(box.get("photo_path") and Path(box["photo_path"]).exists())
    zone      = box.get("zone") or "—"
    rack      = box.get("rack_id") or "—"
    last_seen_raw = box.get("last_seen") or ""
    last_seen_str = last_seen_raw[:16].replace("T", " ") if last_seen_raw else "—"
    last_rfid = (box.get("last_rfid_accessed") or "")[:16].replace("T", " ")

    # State styling: color, background-tint, glow
    _ss = {
        "DOCKED":   ("#00ff80", "rgba(0,255,128,.10)",  "0 0 28px rgba(0,255,128,.35)"),
        "AWAY":     ("#f59e0b", "rgba(245,158,11,.10)",  "0 0 28px rgba(245,158,11,.35)"),
        "SET_DOWN": ("#ffff00", "rgba(255,255,0,.07)",   "0 0 28px rgba(255,255,0,.25)"),
        "DOCKING":  ("#00d4ff", "rgba(0,212,255,.10)",   "0 0 28px rgba(0,212,255,.35)"),
    }
    sc, sbg, sglow = _ss.get(state, ("#888888", "rgba(100,100,100,.08)", "none"))

    # Battery
    is_passive = state in ("PASSIVE", "UNKNOWN") and pct < 0
    bat_width  = max(0, min(100, pct)) if pct >= 0 else 0
    bat_color  = "#ff4444" if pct < 20 else "#f59e0b" if pct < 50 else "#00ff80"
    bat_str    = f"{pct:.0f}%" if pct >= 0 else "—"
    bat_section = "" if is_passive else f"""
  <div class="bat-sec">
    <div class="bat-row">
      <span class="bat-label">BATTERY</span>
      <span class="bat-pct" style="color:{bat_color};">{bat_str}</span>
    </div>
    <div class="bat-track"><div class="bat-fill"
      style="width:{bat_width}%;background:{bat_color};"></div></div>
  </div>"""

    # RFID last tap
    rfid_row = (f'<div class="meta-kv"><span class="mk">Last NFC Tap</span>'
                f'<span class="mv">{last_rfid}</span></div>' if last_rfid else "")

    # Via-RFID JS (fire-and-forget ping + strip query param)
    via_js = (f'fetch("/box/{box_id}/rfid-ping",{{method:"POST"}}).catch(()=>{{}});'
              f'history.replaceState({{}},"","/box/{box_id}");') if via == "rfid" else ""

    # Photo
    photo_html = (f'<img id="photo-img" src="/api/boxes/{box_id}/photo?t=0" alt="Interior"'
                  f' onerror="this.style.display=\'none\';'
                  f'document.getElementById(\'no-photo\').style.display=\'flex\'">'
                  if has_photo else "")
    no_photo_display = "none" if has_photo else "flex"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#09111f">
<title>{name} — SmartToolbox</title>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}}
:root{{
  --bg:#09111f;--bg2:#060b15;--bd:#1e3a5f;--bd2:#0e1d2e;
  --orange:#e36b00;--cyan:#00d4ff;--text:#c8d8e8;--muted:#334155;
  --fd:'Barlow Condensed',sans-serif;--fm:'Share Tech Mono',monospace;
}}
body{{background:var(--bg);color:var(--text);font-family:var(--fm);
  max-width:480px;margin:0 auto;min-height:100vh;
  padding-bottom:calc(64px + env(safe-area-inset-bottom));}}
/* Header */
.hdr{{background:var(--bg2);border-bottom:1px solid var(--bd);}}
.stripe{{height:5px;background:var(--orange);}}
.nasa-band{{display:flex;align-items:center;gap:12px;padding:10px 16px;}}
.meatball{{width:52px;height:52px;flex-shrink:0;}}
.hdr-txt{{flex:1;}}
.back{{font-size:10px;color:var(--orange);letter-spacing:2px;
  text-decoration:none;opacity:.8;display:inline-block;margin-bottom:3px;}}
.bid{{font-family:var(--fm);font-size:1rem;color:var(--cyan);letter-spacing:3px;}}
.cat-badge{{display:inline-block;margin-top:4px;font-size:1rem;font-weight:700;
  letter-spacing:2px;text-transform:uppercase;color:var(--orange);
  border:1px solid var(--orange);padding:2px 10px;}}
/* Name hero */
.name-hero{{padding:14px 16px 10px;border-bottom:1px solid var(--bd2);}}
.box-name{{font-family:var(--fd);font-size:2.8rem;font-weight:900;
  color:#fff;text-transform:uppercase;letter-spacing:-1px;line-height:1;}}
.meta-row{{display:flex;gap:20px;margin-top:8px;flex-wrap:wrap;}}
.meta-kv{{display:flex;flex-direction:column;}}
.mk{{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--muted);}}
.mv{{font-size:13px;font-weight:700;color:var(--cyan);letter-spacing:.5px;}}
/* State block — centerpiece */
.state-block{{padding:20px 16px;border-bottom:1px solid var(--bd2);
  display:flex;flex-direction:column;align-items:center;gap:10px;}}
.state-hero{{display:inline-flex;align-items:center;gap:14px;
  padding:14px 32px;font-family:var(--fd);font-size:2.2rem;font-weight:900;
  letter-spacing:5px;text-transform:uppercase;border:2px solid;}}
.state-dot{{width:10px;height:10px;border-radius:50%;background:currentColor;
  box-shadow:0 0 8px currentColor;animation:blink 2s infinite;flex-shrink:0;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.state-sub{{font-size:10px;color:var(--muted);letter-spacing:2px;text-align:center;}}
</style>
/* Battery */
.bat-sec{{padding:12px 16px;border-bottom:1px solid var(--bd2);}}
.bat-row{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}}
.bat-label{{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);}}
.bat-pct{{font-family:var(--fd);font-size:1.3rem;font-weight:900;letter-spacing:1px;}}
.bat-track{{height:6px;background:var(--bd);border-radius:3px;overflow:hidden;}}
.bat-fill{{height:100%;border-radius:3px;transition:width .5s;}}
/* Section shell */
.sec{{padding:14px 16px;border-bottom:1px solid var(--bd2);}}
.sec-title{{font-size:9px;color:var(--muted);letter-spacing:3px;
  text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:8px;}}
.sec-badge{{font-family:var(--fd);font-size:.9rem;font-weight:700;
  color:var(--cyan);letter-spacing:1px;}}
/* Photo */
.photo-wrap{{position:relative;width:100%;aspect-ratio:4/3;background:var(--bg2);
  border:1px solid var(--bd);overflow:hidden;cursor:pointer;}}
.photo-wrap img{{width:100%;height:100%;object-fit:cover;display:block;}}
.no-photo{{position:absolute;inset:0;display:{no_photo_display};flex-direction:column;
  align-items:center;justify-content:center;gap:8px;color:var(--bd);}}
.no-photo svg{{opacity:.4;}}
.no-photo span{{font-size:11px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}}
.photo-hint{{font-size:10px;color:var(--muted);text-align:center;margin-top:6px;letter-spacing:1px;}}
/* Inventory */
.inv-item{{display:flex;align-items:flex-start;gap:10px;
  padding:8px 0;border-bottom:1px solid var(--bd2);}}
.inv-item:last-child{{border-bottom:none;}}
.inv-bullet{{width:5px;height:5px;background:var(--orange);flex-shrink:0;margin-top:5px;}}
.inv-text{{font-size:13px;color:var(--text);line-height:1.5;}}
.inv-empty{{font-size:12px;color:var(--muted);padding:4px 0;letter-spacing:1px;}}
textarea{{width:100%;min-height:140px;background:var(--bg2);border:1px solid var(--bd);
  color:var(--text);font-family:var(--fm);font-size:13px;
  padding:10px;resize:vertical;line-height:1.7;outline:none;}}
textarea:focus{{border-color:var(--cyan);}}
/* Buttons */
.btn{{display:inline-block;padding:9px 18px;background:var(--orange);color:#fff;
  font-family:var(--fm);font-size:12px;font-weight:bold;letter-spacing:3px;
  border:none;cursor:pointer;text-transform:uppercase;}}
.btn:active{{background:#c05a00;}}
.btn-ghost{{background:transparent;border:1px solid var(--bd);color:var(--cyan);}}
.btn-ghost:active{{background:var(--bd);}}
.btn-ok{{background:#00ff80!important;color:#000!important;}}
/* Events */
.ev{{background:var(--bg2);border:1px solid var(--bd2);padding:8px 12px;margin-bottom:6px;}}
.ev-top{{display:flex;justify-content:space-between;}}
.ev-type{{font-size:10px;color:var(--cyan);letter-spacing:2px;}}
.ev-time{{font-size:10px;color:var(--muted);}}
.ev-data{{font-size:11px;color:var(--muted);margin-top:2px;}}
/* Footer */
.footer{{padding:10px 16px;display:flex;justify-content:space-between;
  font-size:9px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}}
/* Toast */
.toast{{position:fixed;bottom:72px;left:50%;transform:translateX(-50%);
  background:var(--orange);color:#fff;padding:8px 20px;font-size:12px;
  font-weight:bold;letter-spacing:2px;opacity:0;
  transition:opacity .3s;pointer-events:none;z-index:200;}}
.toast.show{{opacity:1;}}
/* Bottom nav */
.bnav{{position:fixed;bottom:0;left:0;right:0;max-width:480px;margin:0 auto;
  background:var(--bg2);border-top:1px solid var(--bd);
  display:flex;justify-content:space-around;
  padding:8px 0 max(8px,env(safe-area-inset-bottom));}}
.ni{{display:flex;flex-direction:column;align-items:center;gap:2px;
  text-decoration:none;font-size:9px;letter-spacing:2px;
  text-transform:uppercase;color:var(--muted);padding:4px 16px;cursor:pointer;
  background:none;border:none;}}
.ni.on{{color:var(--cyan);}}
.ni svg{{width:20px;height:20px;stroke:currentColor;stroke-width:1.5;fill:none;}}
/* Scan button + spinner */
.scan-bar{{display:flex;align-items:center;gap:8px;margin-bottom:12px;}}
.btn-scan{{background:var(--cyan);color:#000;}}
.btn-scan:active{{background:#00aacc;}}
.btn-scan:disabled{{opacity:.5;cursor:default;}}
.spinner{{display:none;width:16px;height:16px;border:2px solid var(--bd);
  border-top-color:var(--cyan);border-radius:50%;animation:spin .7s linear infinite;flex-shrink:0;}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.scan-status{{font-size:11px;color:var(--muted);letter-spacing:1px;}}
#scan-file{{display:none;}}
</style>
</head>
<body>

<div class="hdr">
  <div class="stripe"></div>
  <div class="nasa-band">
    <img class="meatball" src="/client/assets/nasa-meatball.svg" alt=""
         onerror="this.style.display='none'">
    <div class="hdr-txt">
      <a class="back" href="/m" id="back-link">&#x2190; BACK</a><br>
      <span class="bid">{box_id}</span><br>
      <span class="cat-badge">{category}</span>
    </div>
  </div>
</div>

<div class="name-hero">
  <div class="box-name">{name}</div>
  <div class="meta-row">
    <div class="meta-kv"><span class="mk">Zone</span><span class="mv">{zone}</span></div>
    <div class="meta-kv"><span class="mk">Rack</span><span class="mv">{rack}</span></div>
    {rfid_row}
  </div>
</div>

<div class="state-block">
  <div class="state-hero" id="state-hero"
       style="color:{sc};background:{sbg};border-color:{sc};box-shadow:{sglow};">
    <div class="state-dot"></div>
    <span id="state-label">{state}</span>
  </div>
  <div class="state-sub" id="last-seen-sub">Last seen: {last_seen_str}</div>
</div>

{bat_section}

<div class="sec">
  <div class="sec-title">Interior Photo</div>
  <div class="photo-wrap" onclick="document.getElementById('file-input').click()">
    {photo_html}
    <div class="no-photo" id="no-photo">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <rect x="2" y="4" width="20" height="16" rx="2"/>
        <circle cx="12" cy="12" r="4"/>
        <path d="M8 4l1.5-2h5L16 4"/>
      </svg>
      <span>Tap to add photo</span>
    </div>
  </div>
  <div class="photo-hint">Tap photo to replace</div>
  <input type="file" id="file-input" accept="image/*" capture="environment">
</div>

<div class="sec">
  <div class="sec-title">
    Inventory Manifest
    <span class="sec-badge" id="inv-count"></span>
  </div>
  <div class="scan-bar">
    <button class="btn btn-scan" id="scan-btn"
            onclick="document.getElementById('scan-file').click()">&#x1F4F7; Scan Contents</button>
    <div class="spinner" id="scan-spin"></div>
    <span class="scan-status" id="scan-status"></span>
  </div>
  <input type="file" id="scan-file" accept="image/*" capture="environment">
  <div id="inv-read">
    <div id="inv-list"></div>
    <div id="inv-empty" style="display:none;" class="inv-empty">No items — tap Edit to add inventory.</div>
    <div style="margin-top:10px;">
      <button class="btn btn-ghost" onclick="showEdit()">Edit Manifest</button>
    </div>
  </div>
  <div id="inv-edit" style="display:none;">
    <textarea id="inv-ta" placeholder="One item per line">{inventory}</textarea>
    <div style="display:flex;gap:8px;margin-top:8px;">
      <button class="btn" id="save-btn" onclick="saveInv()">Save</button>
      <button class="btn btn-ghost" onclick="cancelEdit()">Cancel</button>
    </div>
  </div>
</div>

<div class="sec">
  <div class="sec-title">Event Log</div>
  <div id="evt-log"></div>
</div>

<div class="footer">
  <span>SMARTTOOLBOX // {box_id}</span>
  <span>MOB-V2</span>
</div>
<div class="toast" id="toast"></div>

<nav class="bnav">
  <button class="ni" onclick="document.getElementById('file-input').click()">
    <svg viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/>
      <circle cx="12" cy="12" r="4"/><path d="M8 4l1.5-2h5L16 4"/></svg>Photo</button>
  <button class="ni on" onclick="showEdit()">
    <svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>Edit</button>
  <a class="ni" href="/m">
    <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>Fleet</a>
</nav>

<script>
const BOX_ID="{box_id}";
{via_js}
// Back button: use browser history if available, else fall back to fleet
(function(){{
  const a=document.getElementById('back-link');
  if(document.referrer && document.referrer!==location.href){{
    a.onclick=e=>{{e.preventDefault();history.back();}};
  }}
  // href="/m" already set — no else needed
}})();
// Photo upload
document.getElementById('file-input').addEventListener('change',async e=>{{
  const f=e.target.files[0]; if(!f) return;
  const fd=new FormData(); fd.append('file',f);
  const r=await fetch(`/api/boxes/${{BOX_ID}}/photo`,{{method:'POST',body:fd}});
  if(r.ok){{
    const ts=Date.now(), img=document.getElementById('photo-img');
    if(img){{img.src=`/api/boxes/${{BOX_ID}}/photo?t=${{ts}}`;img.style.display='block';}}
    else{{
      const w=document.querySelector('.photo-wrap'),ni=document.createElement('img');
      ni.id='photo-img'; ni.src=`/api/boxes/${{BOX_ID}}/photo?t=${{ts}}`; ni.alt='Interior';
      w.insertBefore(ni,w.firstChild);
    }}
    const np=document.getElementById('no-photo'); if(np) np.style.display='none';
    toast('Photo saved');
  }}
}});
// Inventory
const RAW={repr(inventory)};
function renderRead(txt){{
  const items=(txt||'').split('\\n').map(s=>s.trim()).filter(Boolean);
  const L=document.getElementById('inv-list'),E=document.getElementById('inv-empty'),
        C=document.getElementById('inv-count');
  if(!items.length){{L.innerHTML='';E.style.display='block';C.textContent='';}}
  else{{
    E.style.display='none';
    C.textContent=`(${{items.length}})`;
    L.innerHTML=items.map(i=>{{
      const isAI=i.startsWith('[AI]');
      const label=isAI?i.slice(4).trim():i;
      const tag=isAI?'<span style="font-size:9px;color:var(--cyan);letter-spacing:1px;margin-left:6px;border:1px solid var(--cyan);padding:1px 5px;">AI</span>':'';
      return `<div class="inv-item"><div class="inv-bullet"></div>
        <div class="inv-text">${{label}}${{tag}}</div></div>`;
    }}).join('');
  }}
}}
function showEdit(){{
  document.getElementById('inv-read').style.display='none';
  document.getElementById('inv-edit').style.display='block';
  document.getElementById('inv-ta').focus();
}}
function cancelEdit(){{
  document.getElementById('inv-ta').value=RAW;
  document.getElementById('inv-edit').style.display='none';
  document.getElementById('inv-read').style.display='block';
}}
async function saveInv(){{
  const txt=document.getElementById('inv-ta').value,
        btn=document.getElementById('save-btn');
  const r=await fetch(`/api/boxes/${{BOX_ID}}/inventory`,{{
    method:'PUT',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{inventory:txt}})
  }});
  if(r.ok){{
    btn.classList.add('btn-ok'); btn.textContent='SAVED ✓';
    toast('Inventory saved'); renderRead(txt);
    setTimeout(()=>{{btn.classList.remove('btn-ok');btn.textContent='Save';cancelEdit();}},1800);
  }}
}}
renderRead(RAW);
// AI Scan
document.getElementById('scan-file').addEventListener('change',async e=>{{
  const f=e.target.files[0]; if(!f) return;
  const btn=document.getElementById('scan-btn'),
        spin=document.getElementById('scan-spin'),
        status=document.getElementById('scan-status');
  btn.disabled=true; spin.style.display='block'; status.textContent='Scanning…';
  try{{
    const fd=new FormData(); fd.append('file',f);
    const r=await fetch(`/box/${{BOX_ID}}/ai-scan`,{{method:'POST',body:fd}});
    const data=await r.json();
    if(r.ok && data.ok){{
      const n=data.new_items.length;
      status.textContent=n?`${{n}} item${{n!==1?'s':''}} added`:'Nothing new detected';
      if(n){{
        renderRead(data.inventory);
        // also refresh the hidden textarea for edit view
        document.getElementById('inv-ta').value=data.inventory;
        toast(`AI found ${{n}} new item${{n!==1?'s':''}}`);
      }}
    }}else{{
      status.textContent=data.detail||'Scan failed';
    }}
  }}catch(err){{
    status.textContent='Network error';
  }}finally{{
    btn.disabled=false; spin.style.display='none';
    e.target.value='';
    setTimeout(()=>status.textContent='',4000);
  }}
}});
// Live state refresh
(async()=>{{
  try{{
    const r=await fetch(`/api/boxes/${{BOX_ID}}`); if(!r.ok) return;
    const b=await r.json();
    const CS={{DOCKED:['#00ff80','rgba(0,255,128,.10)','0 0 28px rgba(0,255,128,.35)'],
                AWAY:  ['#f59e0b','rgba(245,158,11,.10)','0 0 28px rgba(245,158,11,.35)'],
                SET_DOWN:['#ffff00','rgba(255,255,0,.07)','0 0 28px rgba(255,255,0,.25)'],
                DOCKING: ['#00d4ff','rgba(0,212,255,.10)','0 0 28px rgba(0,212,255,.35)']}};
    const s=(b.state||'UNKNOWN').toUpperCase(),[c,bg,gl]=CS[s]||['#888','rgba(100,100,100,.08)','none'];
    const h=document.getElementById('state-hero'),l=document.getElementById('state-label');
    if(h){{h.style.color=c;h.style.background=bg;h.style.borderColor=c;h.style.boxShadow=gl;}}
    if(l) l.textContent=s;
    if(b.last_seen){{
      const ls=document.getElementById('last-seen-sub');
      if(ls) ls.textContent='Last seen: '+b.last_seen.slice(0,16).replace('T',' ');
    }}
  }}catch(e){{}}
}})();
</script>
// Event log
(async()=>{{
  try{{
    const r=await fetch(`/api/boxes/${{BOX_ID}}/events?limit=20`);
    if(!r.ok) return;
    const evts=await r.json(),log=document.getElementById('evt-log');
    if(!evts.length){{log.innerHTML='<div style="font-size:12px;color:#334155;">No events yet</div>';return;}}
    log.innerHTML=evts.map(e=>{{
      const t=new Date(e.ts).toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
      return `<div class="ev"><div class="ev-top">
        <span class="ev-type">${{e.event_type.toUpperCase()}}</span>
        <span class="ev-time">${{t}}</span></div>
        <div class="ev-data">${{JSON.stringify(e.payload).slice(0,80)}}</div></div>`;
    }}).join('');
  }}catch(e){{}}
}})();
function toast(msg){{
  const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2200);
}}
</script>
</body></html>"""
    return HTMLResponse(html)
