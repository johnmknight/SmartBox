# server/routes/rfid.py
# RFID provisioning dashboard and NFC write pages.
# Provision flow: GET /provision → GET /provision/{box_id}/write → POST /provision/{box_id}/confirm
import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from server.database import get_db

router = APIRouter()

SERVER_IP   = os.getenv("NFC_HOST", os.getenv("SERVER_HOST", "192.168.4.47"))
SERVER_PORT = int(os.getenv("NFC_PORT", os.getenv("SERVER_PORT", "8091")))

_FONTS = """<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">"""

_BASE_CSS = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #09111f; color: #c8d8e8;
       font-family: 'Share Tech Mono', 'Courier New', monospace;
       max-width: 640px; margin: 0 auto; min-height: 100vh; }
.stripe { height: 6px; background: #e36b00; width: 100%; }
.nasa-band {
  background: #060b15; border-bottom: 1px solid #1e3a5f;
  padding: 12px 16px; display: flex; align-items: center; gap: 14px;
}
.nasa-meatball { width: 48px; height: 48px; flex-shrink: 0; }
.page-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.6rem; font-weight: 900; color: #fff;
  text-transform: uppercase; letter-spacing: 2px; line-height: 1.1;
}
.page-sub { font-size: 10px; color: #334155; letter-spacing: 2px; margin-top: 2px; }
.back-link { font-size: 10px; color: #e36b00; letter-spacing: 2px; text-decoration: none; }

.section { padding: 14px 16px; border-bottom: 1px solid #0e1d2e; }
.section-title { font-size: 9px; color: #334155; letter-spacing: 3px;
                 text-transform: uppercase; margin-bottom: 10px; }

.box-row {
  display: flex; align-items: center; justify-content: space-between;
  background: #060b15; border: 1px solid #1e3a5f;
  padding: 10px 14px; margin-bottom: 8px; gap: 12px;
}
.box-row:last-child { margin-bottom: 0; }
.box-row-info { flex: 1; min-width: 0; }
.box-row-id { font-size: 12px; color: #00d4ff; letter-spacing: 2px; }
.box-row-name { font-size: 14px; font-weight: 700; color: #fff;
                font-family: 'Barlow Condensed', sans-serif; letter-spacing: 1px; }
.box-row-ts { font-size: 10px; color: #334155; margin-top: 2px; }

.badge { display: inline-block; padding: 2px 10px; font-size: 10px; font-weight: bold;
         letter-spacing: 2px; border: 1px solid; text-transform: uppercase; }
.badge-ok { color: #00FF80; border-color: #00FF80; }
.badge-warn { color: #F59E0B; border-color: #F59E0B; }

.btn { display: inline-block; padding: 8px 18px; background: #e36b00; color: #fff;
       font-family: 'Share Tech Mono', monospace; font-size: 11px; font-weight: bold;
       letter-spacing: 2px; border: none; cursor: pointer; text-transform: uppercase;
       text-decoration: none; white-space: nowrap; }
.btn:active, .btn:hover { background: #c05a00; }
.btn-ghost { background: transparent; border: 1px solid #1e3a5f; color: #00d4ff; }
.btn-ghost:hover { border-color: #00d4ff; background: transparent; }
.btn-success { background: #00FF80 !important; color: #000 !important; }
.btn-full { display: block; width: 100%; text-align: center; padding: 14px; font-size: 13px; }

.uri-box {
  background: #060b15; border: 1px solid #1e3a5f;
  padding: 12px 14px; font-size: 12px; color: #00d4ff;
  word-break: break-all; line-height: 1.6; letter-spacing: 1px;
  position: relative;
}
.status-msg { padding: 12px 16px; font-size: 12px; letter-spacing: 2px; text-align: center; display: none; }
.status-ok { color: #00FF80; border: 1px solid #00FF80; }
.status-err { color: #FF4444; border: 1px solid #FF4444; }
.divider { border: none; border-top: 1px solid #1e3a5f; margin: 16px 0; }
.steps { padding: 0; list-style: none; }
.steps li { padding: 8px 0; font-size: 12px; color: #c8d8e8;
            border-bottom: 1px solid #0e1d2e; display: flex; gap: 12px; align-items: flex-start; }
.steps li:last-child { border-bottom: none; }
.step-num { color: #e36b00; font-weight: bold; flex-shrink: 0; min-width: 20px; }
.nasa-footer { padding: 10px 16px; display: flex; justify-content: space-between;
               font-size: 9px; color: #1e3a5f; letter-spacing: 2px; text-transform: uppercase; }
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
         background: #e36b00; color: #fff; padding: 8px 20px;
         font-size: 12px; font-weight: bold; letter-spacing: 2px;
         opacity: 0; transition: opacity 0.3s; pointer-events: none; z-index: 100; }
.toast.show { opacity: 1; }
.stats-row { display: flex; gap: 24px; padding: 12px 16px; border-bottom: 1px solid #0e1d2e; }
.stat-item { display: flex; flex-direction: column; }
.stat-key { font-size: 9px; color: #334155; letter-spacing: 2px; text-transform: uppercase; }
.stat-val { font-size: 1.8rem; font-family: 'Barlow Condensed', sans-serif;
            font-weight: 900; color: #fff; }
</style>
"""


# ── Provision Dashboard ────────────────────────────────────────────────────

@router.get("/provision", response_class=HTMLResponse)
async def provision_dashboard(db=Depends(get_db)):
    async with db.execute(
        "SELECT box_id, display_name, rfid_provisioned, rfid_provisioned_at FROM boxes ORDER BY box_id"
    ) as cur:
        boxes = [dict(r) for r in await cur.fetchall()]

    total = len(boxes)
    done  = sum(1 for b in boxes if b["rfid_provisioned"])

    rows_html = ""
    for b in boxes:
        bid    = b["box_id"]
        name   = b.get("display_name") or bid
        prov   = b["rfid_provisioned"]
        prov_at = (b.get("rfid_provisioned_at") or "")[:16].replace("T", " ")

        badge  = '<span class="badge badge-ok">✓ PROVISIONED</span>' if prov \
                 else '<span class="badge badge-warn">⚠ UNPROVISIONED</span>'
        ts_str = f'<div class="box-row-ts">Tagged: {prov_at}</div>' if prov_at else ""
        btn    = (f'<a class="btn btn-ghost" href="/provision/{bid}/write">Reprovision</a>' if prov
                  else f'<a class="btn" href="/provision/{bid}/write">Write Tag</a>')

        rows_html += f"""
        <div class="box-row">
          <div class="box-row-info">
            <div class="box-row-id">{bid}</div>
            <div class="box-row-name">{name}</div>
            {ts_str}
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
            {badge}
            {btn}
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>NFC Provision — SmartToolbox</title>
{_FONTS}
{_BASE_CSS}
</head>
<body>
<div class="stripe"></div>
<div class="nasa-band">
  <img class="nasa-meatball" src="/client/assets/nasa-meatball.svg" alt="" onerror="this.style.display='none'">
  <div>
    <a class="back-link" href="/">&#x2190; DASHBOARD</a>
    <div class="page-title">NFC Provision</div>
    <div class="page-sub">NTAG215 TAG MANAGEMENT</div>
  </div>
</div>

<div class="stats-row">
  <div class="stat-item"><span class="stat-key">Total Boxes</span><span class="stat-val">{total}</span></div>
  <div class="stat-item"><span class="stat-key">Provisioned</span><span class="stat-val" style="color:#00FF80;">{done}</span></div>
  <div class="stat-item"><span class="stat-key">Remaining</span><span class="stat-val" style="color:#F59E0B;">{total - done}</span></div>
</div>

<div class="section">
  <div class="section-title">All Boxes</div>
  {rows_html}
</div>

<div class="nasa-footer">
  <span>SMARTTOOLBOX // RFID OPS</span>
  <span>NFC-PROVISION-V1</span>
</div>
</body>
</html>"""
    return HTMLResponse(html)


# ── Provision Write Page ───────────────────────────────────────────────────

@router.get("/provision/{box_id}/write", response_class=HTMLResponse)
async def provision_write_page(box_id: str, db=Depends(get_db)):
    async with db.execute("SELECT * FROM boxes WHERE box_id=?", (box_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, f"Box '{box_id}' not found")
    box = dict(row)
    name = box.get("display_name") or box_id
    tag_uri = f"http://{SERVER_IP}:{SERVER_PORT}/box/{box_id}?via=rfid"

    async with db.execute(
        "SELECT box_id FROM boxes WHERE (rfid_provisioned IS NULL OR rfid_provisioned=0) AND box_id != ? ORDER BY box_id LIMIT 1",
        (box_id,)
    ) as cur:
        nxt = await cur.fetchone()
    next_box_id = nxt["box_id"] if nxt else None
    next_btn = (f'<a class="btn btn-full" href="/provision/{next_box_id}/write">Next Unprovisioned Box &#x2192;</a>'
                if next_box_id else
                '<div class="status-msg status-ok">&#x2713; ALL BOXES PROVISIONED</div>')

    already_provisioned = bool(box.get("rfid_provisioned"))
    prov_badge = (
        '<span class="badge badge-ok" style="margin-top:4px;">&#x2713; ALREADY PROVISIONED — REWRITING</span>'
        if already_provisioned else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Write Tag: {box_id} — SmartToolbox</title>
{_FONTS}
{_BASE_CSS}
</head>
<body>
<div class="stripe"></div>
<div class="nasa-band">
  <img class="nasa-meatball" src="/client/assets/nasa-meatball.svg" alt="" onerror="this.style.display='none'">
  <div>
    <a class="back-link" href="/provision">&#x2190; PROVISION DASHBOARD</a>
    <div class="page-title">Write NFC Tag</div>
    <div class="page-sub">{box_id}</div>
  </div>
</div>

<div class="section">
  <div class="section-title">Target Box</div>
  <div style="font-family:'Barlow Condensed',sans-serif;font-size:2rem;font-weight:900;color:#fff;letter-spacing:1px;">{name}</div>
  <div style="font-size:11px;color:#334155;letter-spacing:2px;margin-top:4px;">{box_id}</div>
  {prov_badge}
</div>

<div class="section">
  <div class="section-title">Tag URI — write this to the tag</div>
  <div class="uri-box" id="uri-display">{tag_uri}</div>
  <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
    <button class="btn" onclick="copyUri()">&#x29C9; Copy URI</button>
    <a class="btn btn-ghost" href="/box/{box_id}" target="_blank">Preview Page &#x2197;</a>
  </div>
</div>

<div class="section">
  <div class="section-title">How to write with NFC Tools app</div>
  <ol class="steps">
    <li><span class="step-num">1.</span>Tap <strong>Copy URI</strong> above to copy the tag URI to your clipboard.</li>
    <li><span class="step-num">2.</span>Open the <strong>NFC Tools</strong> app on your phone (free — iOS &amp; Android).</li>
    <li><span class="step-num">3.</span>Tap <strong>Write</strong> &rarr; <strong>Add a record</strong> &rarr; <strong>URL / URI</strong>.</li>
    <li><span class="step-num">4.</span>Paste the URI &rarr; tap <strong>OK</strong> &rarr; tap <strong>Write / X records</strong>.</li>
    <li><span class="step-num">5.</span>Hold the back of your phone flat against the blank NTAG215 sticker until you feel the success vibration.</li>
    <li><span class="step-num">6.</span>Tap <strong>Mark as Provisioned</strong> below.</li>
  </ol>
</div>

<div class="section">
  <div class="section-title">Verify before marking</div>
  <p style="font-size:12px;color:#c8d8e8;letter-spacing:1px;margin-bottom:14px;line-height:1.7;">
    Tap the freshly-written sticker with your phone to confirm it opens the correct box page, then mark it as provisioned.
  </p>
  <button class="btn btn-full" id="mark-btn" onclick="markProvisioned()">&#x2713; Mark as Provisioned</button>
  <div id="mark-status" style="margin-top:10px;"></div>
</div>

<div id="next-section" style="display:none;padding:16px 16px 0;">
  {next_btn}
</div>

<div class="nasa-footer">
  <span>SMARTTOOLBOX // NFC WRITE</span>
  <span>{box_id}</span>
</div>

<div class="toast" id="toast"></div>

<script>
const _seg=window.location.pathname.split('/')[1]||'';
const API=(!_seg||_seg.includes('.')||['client','api','static','testing','provision','m','scan','mobile'].includes(_seg))?'':'/'+_seg;
if(API)document.querySelectorAll('a[href^="/"]').forEach(function(a){{const h=a.getAttribute('href');if(!h.startsWith('//'))a.setAttribute('href',API+h);}});
const BOX_ID = "{box_id}";
const TAG_URI = "{tag_uri}";

function copyUri() {{
  navigator.clipboard.writeText(TAG_URI)
    .then(() => toast('URI copied to clipboard'))
    .catch(() => {{
      // Fallback for browsers that block clipboard API
      const el = document.getElementById('uri-display');
      const range = document.createRange();
      range.selectNodeContents(el);
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);
      toast('URI selected — copy manually');
    }});
}}

async function markProvisioned() {{
  const btn = document.getElementById('mark-btn');
  btn.disabled = true;
  btn.textContent = '...';
  try {{
    const r = await fetch(API+`/provision/${{BOX_ID}}/confirm`, {{method: 'POST'}});
    if (r.ok) {{
      btn.classList.add('btn-success');
      btn.textContent = '&#x2713; PROVISIONED';
      const status = document.getElementById('mark-status');
      status.className = 'status-msg status-ok';
      status.textContent = '✓ BOX MARKED AS PROVISIONED';
      status.style.display = 'block';
      setTimeout(() => {{
        document.getElementById('next-section').style.display = 'block';
      }}, 800);
    }} else {{
      throw new Error('Server error ' + r.status);
    }}
  }} catch(e) {{
    btn.disabled = false;
    btn.textContent = '&#x2713; Mark as Provisioned';
    const status = document.getElementById('mark-status');
    status.className = 'status-msg status-err';
    status.textContent = '✗ Failed — check server connection and try again';
    status.style.display = 'block';
  }}
}}

function toast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}}
</script>
</body>
</html>"""
    return HTMLResponse(html)


# ── Provision Confirm ──────────────────────────────────────────────────────

@router.post("/provision/{box_id}/confirm")
async def provision_confirm(box_id: str, db=Depends(get_db)):
    async with db.execute("SELECT box_id FROM boxes WHERE box_id=?", (box_id,)) as cur:
        if not await cur.fetchone():
            raise HTTPException(404, f"Box '{box_id}' not found")
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await db.execute(
        "UPDATE boxes SET rfid_provisioned=1, rfid_provisioned_at=? WHERE box_id=?",
        (ts, box_id)
    )
    await db.commit()
    return JSONResponse({"ok": True, "box_id": box_id, "rfid_provisioned": True, "rfid_provisioned_at": ts})
