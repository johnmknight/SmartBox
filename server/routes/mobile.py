# server/routes/mobile.py
# Mobile fleet dashboard — served at /m
# Designed for quick floor-level status checks.
# NFC tag scans still land at /box/{box_id}.
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#09111f">
<title>SmartToolbox</title>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
:root{
  --bg:#09111f; --bg2:#060b15; --border:#1e3a5f; --border2:#0e1d2e;
  --orange:#e36b00; --cyan:#00d4ff; --green:#00ff80;
  --amber:#f59e0b; --yellow:#ffff00; --red:#ff4444;
  --text:#c8d8e8; --muted:#334155;
  --fd:'Barlow Condensed',sans-serif; --fm:'Share Tech Mono',monospace;
}
body{background:var(--bg);color:var(--text);font-family:var(--fm);
  min-height:100vh;padding-bottom:calc(56px + env(safe-area-inset-bottom));}
</style>
<style>
.hdr{background:var(--bg2);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100;}
.hdr-stripe{height:4px;background:var(--orange);}
.hdr-inner{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;}
.wordmark{font-family:var(--fd);font-size:1.3rem;font-weight:900;
  letter-spacing:3px;text-transform:uppercase;color:#fff;}
.wordmark b{color:var(--orange);font-weight:900;}
.hdr-right{display:flex;align-items:center;gap:10px;}
.cdot{width:8px;height:8px;border-radius:50%;background:var(--muted);flex-shrink:0;}
.cdot.live{background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 2s infinite;}
.cdot.err{background:var(--red);animation:none;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}
.rbtn{background:transparent;border:1px solid var(--border);color:var(--muted);
  font-family:var(--fm);font-size:11px;letter-spacing:2px;padding:5px 10px;cursor:pointer;}
.rbtn:active,.rbtn.spin{color:var(--cyan);border-color:var(--cyan);}
/* ── Stats ──────────────────────────────── */
.stats{display:grid;grid-template-columns:repeat(3,1fr);
  border-bottom:1px solid var(--border);background:var(--bg2);}
.stat{display:flex;flex-direction:column;align-items:center;padding:12px 8px;
  border-right:1px solid var(--border2);}
.stat:last-child{border-right:none;}
.stat-n{font-family:var(--fd);font-size:2.6rem;font-weight:900;line-height:1;color:#fff;}
.stat-n.g{color:var(--green);text-shadow:0 0 16px var(--green);}
.stat-n.a{color:var(--amber);text-shadow:0 0 16px var(--amber);}
.stat-l{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-top:3px;}
/* ── Filters ────────────────────────────── */
.filters{display:flex;align-items:center;gap:8px;padding:8px 16px;
  border-bottom:1px solid var(--border2);overflow-x:auto;scrollbar-width:none;}
.filters::-webkit-scrollbar{display:none;}
.chip{flex-shrink:0;padding:5px 12px;font-family:var(--fm);font-size:10px;
  letter-spacing:2px;text-transform:uppercase;border:1px solid var(--border);
  color:var(--muted);background:transparent;cursor:pointer;white-space:nowrap;}
.chip.on{border-color:var(--cyan);color:var(--cyan);background:rgba(0,212,255,.06);}
/* ── Box cards ──────────────────────────── */
.card{display:flex;align-items:stretch;text-decoration:none;color:inherit;
  border-bottom:1px solid var(--border2);background:var(--bg);
  position:relative;transition:background .12s;}
.card:active{background:#0d1a2a;}
.sbar{width:4px;flex-shrink:0;background:var(--muted);}
.card.away   .sbar{background:var(--amber);}
.card.docked .sbar{background:var(--green);}
.card.set_down .sbar{background:var(--yellow);}
.card.docking  .sbar{background:var(--cyan);}
.cbody{flex:1;padding:12px 14px;min-width:0;}
.ctop{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:4px;}
.cname{font-family:var(--fd);font-size:1.25rem;font-weight:700;color:#fff;
  line-height:1.1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;}
.cright{flex-shrink:0;display:flex;flex-direction:column;align-items:flex-end;gap:4px;}
.spill{font-size:9px;font-weight:700;letter-spacing:2px;padding:2px 7px;
  border:1px solid;text-transform:uppercase;}
.spill.away    {color:var(--amber);border-color:var(--amber);}
.spill.docked  {color:var(--green);border-color:var(--green);}
.spill.set_down{color:var(--yellow);border-color:var(--yellow);}
.spill.docking {color:var(--cyan); border-color:var(--cyan);}
.spill.unknown {color:var(--muted);border-color:var(--muted);}
.bat-txt{font-size:10px;color:var(--muted);letter-spacing:1px;}
.bat-txt.lo{color:var(--red);} .bat-txt.mi{color:var(--amber);} .bat-txt.ok{color:var(--green);}
.cmeta{display:flex;align-items:center;gap:7px;margin-top:5px;flex-wrap:wrap;}
.cid{font-size:10px;color:var(--cyan);letter-spacing:2px;}
.ccat{font-size:10px;color:var(--muted);}
.dot3{width:3px;height:3px;border-radius:50%;background:var(--border);flex-shrink:0;}
.cls{font-size:10px;color:var(--muted);margin-left:auto;}
.bbar{height:2px;position:absolute;bottom:0;left:4px;right:0;background:var(--bg2);}
.bfill{height:100%;transition:width .5s;}
.empty{text-align:center;padding:60px 24px;color:var(--muted);}
.etitle{font-family:var(--fd);font-size:1.2rem;font-weight:700;
  letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;}
.esub{font-size:12px;}
/* ── Bottom nav ─────────────────────────── */
.bnav{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);
  border-top:1px solid var(--border);display:flex;justify-content:space-around;
  padding:8px 0 max(8px,env(safe-area-inset-bottom));}
.ni{display:flex;flex-direction:column;align-items:center;gap:2px;
  text-decoration:none;font-size:9px;letter-spacing:2px;
  text-transform:uppercase;color:var(--muted);padding:4px 20px;}
.ni.on{color:var(--cyan);}
.ni svg{width:20px;height:20px;stroke:currentColor;stroke-width:1.5;fill:none;}
</style>
</head>
<body>
<div class="hdr">
  <div class="hdr-stripe"></div>
  <div class="hdr-inner">
    <div class="wordmark">SMART<b>TOOLBOX</b></div>
    <div class="hdr-right">
      <div class="cdot" id="cdot"></div>
      <button class="rbtn" id="rbtn" onclick="doRefresh()">&#x27F3;</button>
    </div>
  </div>
</div>
<div class="stats">
  <div class="stat"><div class="stat-n g" id="sn-docked">—</div><div class="stat-l">Docked</div></div>
  <div class="stat"><div class="stat-n a" id="sn-away">—</div><div class="stat-l">Away</div></div>
  <div class="stat"><div class="stat-n"   id="sn-total">—</div><div class="stat-l">Total</div></div>
</div>
<div class="filters">
  <button class="chip on" onclick="setF('all',this)">All</button>
  <button class="chip"    onclick="setF('away',this)">Away</button>
  <button class="chip"    onclick="setF('docked',this)">Docked</button>
  <button class="chip"    onclick="setF('set_down',this)">Set Down</button>
  <button class="chip"    onclick="setF('low',this)">Low Battery</button>
</div>
<div id="list"><div class="empty"><div class="etitle">Loading…</div></div></div>
<nav class="bnav">
  <a class="ni on" href="/m">
    <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>Fleet</a>
  <a class="ni" href="/provision">
    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/>
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>NFC</a>
  <a class="ni" href="/">
    <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/>
      <path d="M3 9h18M9 21V9"/></svg>Desk</a>
</nav>
<script>
let _boxes=[],_filter='all',_timer=null;
const SO={AWAY:0,SET_DOWN:1,DOCKING:2,DOCKED:3};
async function load(){
  const dot=document.getElementById('cdot'),btn=document.getElementById('rbtn');
  btn.classList.add('spin');
  try{
    const r=await fetch('/api/boxes/');
    if(!r.ok) throw new Error(r.status);
    _boxes=await r.json();
    dot.className='cdot live';
    stats(); render();
  }catch(e){dot.className='cdot err'; err();}
  finally{btn.classList.remove('spin');}
}
function stats(){
  const dk=_boxes.filter(b=>(b.state||'').toUpperCase()==='DOCKED').length;
  const aw=_boxes.filter(b=>['AWAY','SET_DOWN','DOCKING'].includes((b.state||'').toUpperCase())).length;
  document.getElementById('sn-docked').textContent=dk;
  document.getElementById('sn-away').textContent=aw;
  document.getElementById('sn-total').textContent=_boxes.length;
}
function setF(f,btn){
  _filter=f;
  document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));
  btn.classList.add('on'); render();
}
function vis(){
  let L=[..._boxes];
  if(_filter==='away')    L=L.filter(b=>['AWAY','SET_DOWN','DOCKING'].includes((b.state||'').toUpperCase()));
  if(_filter==='docked')  L=L.filter(b=>(b.state||'').toUpperCase()==='DOCKED');
  if(_filter==='set_down')L=L.filter(b=>(b.state||'').toUpperCase()==='SET_DOWN');
  if(_filter==='low')     L=L.filter(b=>b.battery_pct>=0&&b.battery_pct<25);
  return L.sort((a,b)=>{
    const ao=SO[(a.state||'').toUpperCase()]??99,bo=SO[(b.state||'').toUpperCase()]??99;
    return ao!==bo?ao-bo:(a.display_name||a.box_id).localeCompare(b.display_name||b.box_id);
  });
}
function bc(p){return p<0?null:p<20?'lo':p<50?'mi':'ok';}
function bclr(p){return p<20?'#ff4444':p<50?'#f59e0b':'#00ff80';}
function rel(ts){
  if(!ts)return'';
  try{const d=new Date(ts+(ts.endsWith('Z')?'':'Z')),s=(Date.now()-d)/1e3;
    return s<60?Math.floor(s)+'s':s<3600?Math.floor(s/60)+'m':s<86400?Math.floor(s/3600)+'h':'';
  }catch{return'';}
}
function render(){
  const L=vis(),el=document.getElementById('list');
  if(!L.length){
    el.innerHTML='<div class="empty"><div class="etitle">Nothing Here</div><div class="esub">No boxes match this filter</div></div>';
    return;
  }
  el.innerHTML=L.map(b=>{
    const st=(b.state||'unknown').toUpperCase(),sc=st.toLowerCase(),
          nm=b.display_name||b.box_id,p=b.battery_pct,
          batTxt=p>=0?`<span class="bat-txt ${bc(p)}">${Math.round(p)}%</span>`:'',
          batBar=p>=0?`<div class="bbar"><div class="bfill" style="width:${Math.min(100,Math.max(0,p))}%;background:${bclr(p)};"></div></div>`:'',
          ts=rel(b.last_seen),cat=b.category||'';
    return `<a class="card ${sc}" href="/box/${b.box_id}">
  <div class="sbar"></div>
  <div class="cbody">
    <div class="ctop">
      <div class="cname">${nm}</div>
      <div class="cright"><span class="spill ${sc}">${st}</span>${batTxt}</div>
    </div>
    <div class="cmeta">
      <span class="cid">${b.box_id}</span>
      ${cat?`<div class="dot3"></div><span class="ccat">${cat}</span>`:''}
      ${ts?`<span class="cls">${ts} ago</span>`:''}
    </div>
  </div>${batBar}</a>`;
  }).join('');
}
function err(){
  document.getElementById('list').innerHTML=
    '<div class="empty"><div class="etitle">Offline</div><div class="esub">Tap ↻ to retry</div></div>';
}
function doRefresh(){load();clearInterval(_timer);_timer=setInterval(load,15000);}
doRefresh();
</script>
</body></html>"""

@router.get("/m", response_class=HTMLResponse)
async def mobile_dashboard():
    return HTMLResponse(_HTML)
