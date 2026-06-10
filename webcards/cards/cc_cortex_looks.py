"""cc_cortex_looks.py — the Flow look for the Cortex card (production).

render_flow_card(cards, mesh_url, settings) → full card HTML
(CSS + div + gear + module JS).

Your selected cards' art is stitched into a texture atlas and projected
onto a real ICBM-152 cortical surface via a custom Three.js shader, then
flowed across the brain. A rich gear dial drives it live:

    count · order · pattern · flow speed · brightness ·
    pulse rate · pulse amount · ribbon width · rim glow · spin

The brain mesh is parsed in-browser (gunzip via DecompressionStream +
a tiny .mz3 reader); rendering is Three.js (CDN ES module). No Niivue.

Settings persist to panes.cortex via /set-pref (same as other cards).
"""
from __future__ import annotations

import html as _html
import json as _json

ORDERS = ("value", "color", "recent", "random")
PATTERNS = ("ribbon", "wrap", "spiral", "vertical")


def _seg(fx: str, options: list[tuple[str, str]], current: str) -> str:
    """A segmented button row (label/value pairs); `current` gets .on."""
    btns = "".join(
        f'<button class="cx-fx-btn{" on" if v == current else ""}" '
        f'data-fx="{fx}" data-v="{v}">{lbl}</button>'
        for lbl, v in options)
    return f'<div class="cx-fx-segrow">{btns}</div>'


def _slider(fx: str, lo, hi, step, val, out_fmt: str = "") -> str:
    return (f'<input class="cx-fx-slider" type="range" data-fx="{fx}" '
            f'min="{lo}" max="{hi}" step="{step}" value="{val}">'
            f'<span class="cx-fx-out" data-out="{fx}">{out_fmt}</span>')


def _color(fx: str, val: str, title: str) -> str:
    return (f'<input class="cx-fx-color" type="color" data-fx="{fx}" '
            f'value="{val}" title="{title}">')


def render_flow_card(cards: list[dict], mesh_url: str, settings: dict) -> str:
    cards_attr = _html.escape(_json.dumps(cards), quote=True)
    set_attr = _html.escape(_json.dumps(settings), quote=True)
    s = settings
    gear = f"""
  <button class="card-gear cx-gear-trigger" type="button"
          aria-label="Cortex settings" title="Cortex settings">⚙</button>
  <div class="gear-pop cx-pop" hidden role="dialog" aria-label="Cortex settings">
    <h4>Cortex</h4>
    <div class="cx-fx-row"><span class="cx-fx-label">Cards</span>
      {_slider("count", 3, 24, 1, int(s["count"]))}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Order</span>
      {_seg("order", [("value","value"),("color","color"),
                      ("recent","recent"),("random","random")], s["order"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Pattern</span>
      {_seg("pattern", [("ribbon","ribbon"),("wrap","wrap"),
                        ("spiral","spiral"),("vert","vertical")], s["pattern"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Flow speed</span>
      {_slider("speed", 0, 10, 0.5, s["speed"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Brightness</span>
      {_slider("bright", 0.4, 2.0, 0.05, s["bright"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Legibility</span>
      {_slider("legible", 0, 1, 0.05, s.get("legible", 0.55))}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Pulse rate</span>
      {_slider("pulseRate", 0, 6, 0.2, s["pulseRate"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Pulse amount</span>
      {_slider("pulseAmt", 0, 1, 0.05, s["pulseAmt"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Ribbon width</span>
      {_slider("band", 0.15, 1.0, 0.05, s["band"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Rim glow</span>
      {_slider("rim", 0, 1.2, 0.05, s["rim"])}</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Spin</span>
      {_seg("spin", [("on","on"),("off","off")], s["spin"])}</div>
    <div class="cx-fx-sep">Stage lights</div>
    <div class="cx-fx-row"><span class="cx-fx-label">Corner hues</span>
      <span class="cx-lights">
        {_color("lightTL", s.get("lightTL","#000000"), "top-left")}
        {_color("lightTR", s.get("lightTR","#000000"), "top-right")}
        {_color("lightBL", s.get("lightBL","#000000"), "bottom-left")}
        {_color("lightBR", s.get("lightBR","#000000"), "bottom-right")}
      </span></div>
  </div>"""

    return f"""
{_FLOW_CSS}
<div class="card cortex-card cortex-flow"
     data-cortex-cards='{cards_attr}'
     data-cortex-mesh="{_html.escape(mesh_url)}"
     data-cortex-settings='{set_attr}'>
  <h3>🧠 Cortex</h3>{gear}
  <div class="cx-stage">
    <canvas class="cx-canvas"></canvas>
    <div class="cx-hint">Drag to rotate · click a card · ⚙ to tune</div>
    <div class="cx-detail" hidden></div>
  </div>
  <div class="cx-foot">your collection, flowing across an ICBM-152 cortex</div>
</div>
<script type="module">{_FLOW_JS}</script>
"""


_FLOW_CSS = """<style>
  .cortex-card { position: relative; padding: 14px; }
  .cortex-flow .cx-stage { position: relative; min-height: 470px; height:100%;
      border-radius: 12px; overflow: hidden;
      background: radial-gradient(ellipse at 50% 38%, #181612 0%,
                  #0e0b08 58%, #060403 100%); }
  /* absolute-fill so the canvas display size always equals the stage box.
     max-height:none overrides the dashboard's global `canvas{max-height:
     300px}` cap — without this the 470px render buffer is squished into a
     300px display box (vertical squish + brain pushed high). */
  .cortex-flow .cx-canvas { position:absolute; inset:0; width:100%; height:100%;
      max-height:none !important; display:block; cursor:grab; }
  .cortex-flow .cx-canvas:active { cursor:grabbing; }
  .cortex-flow .cx-hint { position:absolute; left:0; right:0; bottom:10px;
      text-align:center; font-size:12px; color:#9d9582; letter-spacing:0.4px;
      pointer-events:none; transition:opacity 200ms ease; }
  .cortex-flow .cx-foot { margin-top:10px; text-align:center; font-size:12px;
      color: var(--muted); font-style: italic; }
  /* gear popover */
  .cx-pop { width: 244px; }
  .cx-pop h4 { margin:0 0 8px; font-size:12px; letter-spacing:0.1em;
      text-transform:uppercase; color:var(--gold-2); }
  .cx-fx-row { display:flex; align-items:center; justify-content:space-between;
      gap:8px; margin:7px 0; }
  .cx-fx-label { font-size:11px; color:#cdd5cd; flex:0 0 auto; }
  .cx-fx-segrow { display:inline-flex; border:1px solid rgba(212,175,55,0.3);
      border-radius:6px; overflow:hidden; }
  .cx-fx-btn { font:inherit; font-size:10px; font-weight:700; color:#b9c2b9;
      background:transparent; border:0; cursor:pointer; padding:3px 7px; }
  .cx-fx-btn.on { color:#2a1907; background:linear-gradient(180deg,#e6c780,#c8a247); }
  .cx-fx-slider { flex:1; min-width:64px; accent-color:#c8a247; }
  .cx-fx-out { font-size:11px; color:#cdd5cd; flex:0 0 34px; text-align:right; }
  .cx-fx-sep { margin:10px 0 4px; font-size:10px; letter-spacing:0.12em;
      text-transform:uppercase; color:#8d856e;
      border-top:1px solid rgba(212,175,55,0.18); padding-top:8px; }
  .cx-lights { display:inline-flex; gap:5px; }
  .cx-fx-color { width:22px; height:22px; padding:0; border:1px solid
      rgba(212,175,55,0.4); border-radius:5px; background:none; cursor:pointer; }
  .cx-fx-color::-webkit-color-swatch-wrapper { padding:1px; }
  .cx-fx-color::-webkit-color-swatch { border:none; border-radius:3px; }
  /* dossier — centered, full card info (matches the other cards' detail) */
  .cortex-flow .cx-detail { position:absolute; inset:0; z-index:8;
      display:flex; align-items:center; justify-content:center; gap:22px;
      padding:24px;
      background: linear-gradient(180deg, rgba(18,13,8,0.98), rgba(7,5,3,0.99));
      opacity:0; transform: scale(0.98); pointer-events:none;
      transition: opacity 220ms ease, transform 220ms ease; }
  .cortex-flow .cx-detail.show { opacity:1; transform:scale(1); pointer-events:auto; }
  .cortex-flow .cx-d-card { flex:0 0 auto; width:38%; max-width:230px;
      border-radius:10px; overflow:hidden;
      box-shadow:0 12px 38px rgba(0,0,0,0.7); }
  .cortex-flow .cx-d-card img { width:100%; height:auto; display:block; }
  .cortex-flow .cx-d-info { flex:0 1 430px; min-width:0; display:flex;
      flex-direction:column; align-items:flex-start; text-align:left;
      max-height:100%; overflow-y:auto; }
  .cortex-flow .cx-d-name { font-size:22px; color:#f4e6b8; margin:0 0 6px;
      line-height:1.15; font-weight:700; }
  .cortex-flow .cx-d-typerow { display:flex; align-items:center; gap:8px;
      flex-wrap:wrap; margin:0 0 8px; }
  .cortex-flow .cx-d-type { font-size:12.5px; color:#cfc6ad; font-style:italic; }
  .cx-pips { display:inline-flex; gap:3px; }
  .cx-pip { display:inline-flex; align-items:center; justify-content:center;
      width:17px; height:17px; border-radius:50%; font-size:10px; font-weight:800;
      color:#1a1208; box-shadow:inset 0 0 0 1px rgba(0,0,0,0.35); }
  .cx-pip-c { background:#cdc6b4; color:#2a2218; }
  .cortex-flow .cx-d-meta { font-size:12px; color:#b9b09a; margin:0 0 10px; }
  .cortex-flow .cx-d-meta b { color:#e8dcb8; font-weight:700; }
  .cortex-flow .cx-d-oracle { font-size:12.5px; color:#d8cfb6; line-height:1.55;
      margin:0 0 10px; padding:9px 11px; border-radius:8px;
      background:rgba(212,175,55,0.06); border:1px solid rgba(212,175,55,0.18);
      white-space:pre-wrap; }
  .cortex-flow .cx-d-flavor { font-size:12px; color:#9d9582; line-height:1.5;
      font-style:italic; margin:0 0 10px; padding-left:9px;
      border-left:2px solid rgba(212,175,55,0.3); }
  .cortex-flow .cx-d-artist { font-size:11px; color:#8d856e; margin:0 0 12px; }
  .cortex-flow .cx-d-badges { display:flex; flex-wrap:wrap; gap:6px; margin:0 0 14px; }
  .cx-badge { font-size:10px; font-weight:700; letter-spacing:0.02em;
      padding:3px 9px; border-radius:20px; text-transform:uppercase;
      border:1px solid rgba(255,255,255,0.12); color:#e6ddc6;
      background:rgba(255,255,255,0.04); }
  .cx-badge-res { color:#f2c14e; border-color:rgba(242,193,78,0.5);
      background:rgba(242,193,78,0.10); }
  .cx-badge-fmt { color:#9fc3e8; border-color:rgba(120,170,220,0.4); }
  .cx-badge-rep { color:#e89a6a; border-color:rgba(224,140,80,0.45);
      background:rgba(224,140,80,0.10); }
  .cortex-flow .cx-d-close { margin-top:auto; align-self:flex-start;
      cursor:pointer; background:transparent;
      border:1px solid rgba(233,200,118,0.5); color:#f4e6b8; font:inherit;
      font-size:12px; padding:6px 14px; border-radius:8px; }
  .cortex-flow .cx-d-close:hover { background: rgba(233,200,118,0.12); }
  @media (max-width:600px){ .cortex-flow .cx-detail{flex-direction:column; gap:14px;}
      .cortex-flow .cx-d-card{width:46%;} .cortex-flow .cx-d-info{flex-basis:auto;} }
</style>"""


_FLOW_JS = r"""
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const all = document.querySelectorAll('.cortex-flow');
const root = all[all.length - 1];
if (root && !root.__cxBound) {
  root.__cxBound = true;
  let pool = [], S = {};
  try { pool = JSON.parse(root.getAttribute('data-cortex-cards')) || []; } catch(e){}
  try { S = JSON.parse(root.getAttribute('data-cortex-settings')) || {}; } catch(e){}
  const meshUrl = root.getAttribute('data-cortex-mesh');
  const stage  = root.querySelector('.cx-stage');
  const canvas = root.querySelector('.cx-canvas');
  const detail = root.querySelector('.cx-detail');
  const hint   = root.querySelector('.cx-hint');

  // ── settings state (seeded from saved prefs) ─────────────────────
  const st = {
    count: +S.count||12, order:S.order||'value', pattern:S.pattern||'ribbon',
    speed:+S.speed||5, bright:+S.bright||1.15,
    pulseRate:+S.pulseRate||0, pulseAmt:+S.pulseAmt||0,
    band:+S.band||0.66, rim:(S.rim==null?0.5:+S.rim), spin:(S.spin||'on') };
  const PAT = {ribbon:0, wrap:1, spiral:2, vertical:3};

  // ── persistence (debounced /set-pref, section 'cortex') ──────────
  const pending={}; let saveT=null;
  function queueSave(k,v){ pending[k]=v; if(saveT)clearTimeout(saveT);
    saveT=setTimeout(()=>{ const e=Object.entries(pending);
      for(const k of Object.keys(pending))delete pending[k];
      for(const [key,value] of e){ try{ fetch('/set-pref',{method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({section:'cortex',key,value})});}catch(_){}} },500); }

  // ── three scaffold ───────────────────────────────────────────────
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(40,1,0.1,100);
  camera.position.set(0,0,4.5); camera.lookAt(0,0,0);
  const group=new THREE.Group(); scene.add(group);
  scene.add(new THREE.AmbientLight(0xffffff,0.55));
  const key=new THREE.DirectionalLight(0xfff3e0,0.85); key.position.set(2.4,3.2,3.6); scene.add(key);
  const rim=new THREE.DirectionalLight(0xffcf72,0.7); rim.position.set(-3.4,1.2,-3.0); scene.add(rim);
  let lastW=0, lastH=0;
  function resize(){ const w=stage.clientWidth|0, h=stage.clientHeight|0;
    if(w<2||h<2||(w===lastW&&h===lastH)) return;
    lastW=w; lastH=h;
    renderer.setSize(w,h,false); camera.aspect=w/h;
    camera.updateProjectionMatrix(); camera.lookAt(0,0,0); }
  resize(); window.addEventListener('resize',resize);
  if(window.ResizeObserver) new ResizeObserver(resize).observe(stage);

  // ── parse the .mz3 brain in-browser ──────────────────────────────
  async function parseMz3(url){
    const resp=await fetch(url); if(!resp.ok) throw new Error('mesh '+resp.status);
    let buf;
    if(typeof DecompressionStream!=='undefined'){
      const ds=new DecompressionStream('gzip');
      buf=await new Response(resp.body.pipeThrough(ds)).arrayBuffer();
    } else buf=await resp.arrayBuffer();
    const dv=new DataView(buf);
    const attr=dv.getUint16(2,true), nface=dv.getUint32(4,true),
          nvert=dv.getUint32(8,true), nskip=dv.getUint32(12,true);
    let off=16+nskip, indices=null, positions=null;
    if(attr&1){ indices=new Uint32Array(buf,off,nface*3).slice(); off+=nface*3*4; }
    if(attr&2){ positions=new Float32Array(buf,off,nvert*3).slice(); off+=nvert*3*4; }
    return {positions,indices};
  }

  // ── card art images (CORS-ok) + atlas ────────────────────────────
  // Route Scryfall art through our same-origin proxy so the canvas/WebGL
  // upload never taints (the Quilt card hit this). On file:// previews
  // there's no server, so load directly (Scryfall does send CORS).
  function proxied(u){
    if(!u) return u;
    if(location.protocol==='file:') return u;
    if(u.indexOf('https://cards.scryfall.io/')===0)
      return '/scryfall-img?url='+encodeURIComponent(u);
    return u;
  }
  function loadImg(u){ return new Promise(res=>{ const im=new Image();
    im.crossOrigin='anonymous'; im.onload=()=>res(im); im.onerror=()=>res(null);
    im.src=proxied(u); }); }
  let images=[];                  // preloaded, indexed to `pool`
  const CW=320, CH=256;
  let atlasCanvas, atlasTex, order=[];   // order: pool indices, current sort

  function computeOrder(){
    let idx = pool.map((_,i)=>i);
    if(st.order==='color'){
      const rank={W:0,U:1,B:2,R:3,G:4,M:5,C:6};
      idx.sort((a,b)=>(rank[pool[a].color]??9)-(rank[pool[b].color]??9));
    } else if(st.order==='recent'){
      idx.sort((a,b)=>(+pool[b].year||0)-(+pool[a].year||0));
    } else if(st.order==='random'){
      // deterministic shuffle (seeded) so it doesn't churn each rebuild
      let seed=1337; const r=()=>{seed=(seed*1103515245+12345)&0x7fffffff;return seed/0x7fffffff;};
      for(let i=idx.length-1;i>0;i--){ const j=(r()*(i+1))|0; [idx[i],idx[j]]=[idx[j],idx[i]]; }
    } // 'value' = as-sent (pool already value-sorted)
    return idx;
  }
  function rebuildAtlas(){
    order=computeOrder();
    const n=Math.max(1, Math.min(st.count, pool.length));
    // Fresh canvas each rebuild — changing a CanvasTexture's source
    // dimensions in place often doesn't re-upload to the GPU (the count
    // slider appeared to do nothing). Build a new canvas + new texture
    // and swap it into the material uniform.
    const cvs=document.createElement('canvas');
    cvs.width=CW*n; cvs.height=CH;
    const g=cvs.getContext('2d');
    g.fillStyle='#15100a'; g.fillRect(0,0,cvs.width,CH);
    for(let i=0;i<n;i++){
      const im=images[order[i]];
      if(im){ const s=Math.max(CW/im.width,CH/im.height);
        const dw=im.width*s, dh=im.height*s;
        g.drawImage(im, i*CW+(CW-dw)/2, (CH-dh)/2, dw, dh); }
    }
    const tex=new THREE.CanvasTexture(cvs);
    tex.colorSpace=THREE.SRGBColorSpace;
    tex.wrapS=THREE.RepeatWrapping; tex.wrapT=THREE.RepeatWrapping;
    if(atlasTex) atlasTex.dispose();
    atlasTex=tex; atlasCanvas=cvs;
    if(mat){ mat.uniforms.uTex.value=atlasTex; mat.uniforms.uN.value=n; }
    activeCount=n;
  }
  let activeCount=st.count;

  // ── dossier ──────────────────────────────────────────────────────
  const MANA_COL={W:'#f5e3a0',U:'#7ab8e2',B:'#a98fb0',R:'#e08868',G:'#7fc08a',C:'#cdc6b4'};
  function esc(s){ return (s==null?'':String(s)).replace(/[&<>]/g,
    m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m])); }
  function manaPips(mc){
    if(!mc) return '';
    const syms=mc.match(/\{[^}]+\}/g)||[];
    if(!syms.length) return '';
    return '<span class="cx-pips">'+syms.map(s=>{
      const k=s.replace(/[{}]/g,'');
      if(/^\d+$/.test(k)||k==='X'||k==='Y') return '<span class="cx-pip cx-pip-c">'+k+'</span>';
      const col=MANA_COL[k]||'#cdc6b4';
      return '<span class="cx-pip" style="background:'+col+'">'+esc(k)+'</span>';
    }).join('')+'</span>';
  }
  const FMT_ORDER=['commander','modern','legacy','vintage','pioneer','pauper','standard'];
  function openDetail(orderPos){
    const c = pool[order[orderPos % activeCount]]; if(!c) return;
    const img=c.image?('<div class="cx-d-card"><a href="'+(c.scryfall_uri||'#')+
      '" target="_blank" rel="noopener"><img src="'+c.image+'" alt="'+esc(c.name)+
      '"></a></div>'):'';
    // meta line
    const mv=(c.cmc!=null && c.cmc!=='')?(' · <b>MV '+c.cmc+'</b>'):'';
    const meta=[c.set, c.year,
      (c.rarity?c.rarity.charAt(0).toUpperCase()+c.rarity.slice(1):''),
      (c.unit?('<b>$'+c.unit+'</b>'):''), (c.qty>1?('×'+c.qty):'')]
      .filter(Boolean).join(' · ')+mv;
    // badges
    let badges='';
    if(c.reserved) badges+='<span class="cx-badge cx-badge-res">Reserved List</span>';
    if(c.reprint_p12!=null){
      const pct=Math.round(c.reprint_p12*100);
      badges+='<span class="cx-badge cx-badge-rep">Reprint risk '+pct+'%</span>';
    }
    const fmts=(c.legalities||[]).filter(f=>FMT_ORDER.includes(f))
      .sort((a,b)=>FMT_ORDER.indexOf(a)-FMT_ORDER.indexOf(b)).slice(0,5);
    for(const f of fmts) badges+='<span class="cx-badge cx-badge-fmt">'+f+'</span>';
    detail.innerHTML=img+'<div class="cx-d-info">'+
      '<h4 class="cx-d-name">'+esc(c.name)+'</h4>'+
      '<div class="cx-d-typerow">'+
        (c.type_line?'<span class="cx-d-type">'+esc(c.type_line)+'</span>':'')+
        manaPips(c.mana_cost)+'</div>'+
      '<p class="cx-d-meta">'+meta+'</p>'+
      (c.oracle_text?'<div class="cx-d-oracle">'+esc(c.oracle_text)+'</div>':'')+
      (c.flavor_text?'<p class="cx-d-flavor">'+esc(c.flavor_text)+'</p>':'')+
      (c.artist?'<p class="cx-d-artist">🖌 '+esc(c.artist)+'</p>':'')+
      (badges?'<div class="cx-d-badges">'+badges+'</div>':'')+
      '<button class="cx-d-close" type="button">← back to the brain</button></div>';
    detail.hidden=false; requestAnimationFrame(()=>detail.classList.add('show'));
    if(hint)hint.style.opacity='0';
    detail.querySelector('.cx-d-close').addEventListener('click',closeDetail);
  }
  function closeDetail(){ detail.classList.remove('show');
    if(hint)hint.style.opacity=''; setTimeout(()=>detail.hidden=true,220); }
  detail.addEventListener('click',e=>{ if(e.target===detail) closeDetail(); });
  document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&!detail.hidden) closeDetail(); });

  // ── drag-orbit + idle auto-spin ──────────────────────────────────
  let yaw=-1.45, pitch=0.0, dragging=false, px=0, py=0, moved=false, idle=0;
  canvas.addEventListener('pointerdown',e=>{ dragging=true; idle=0; px=e.clientX; py=e.clientY;
    moved=false; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove',e=>{ if(!dragging)return;
    const dx=e.clientX-px, dy=e.clientY-py; px=e.clientX; py=e.clientY;
    if(Math.abs(dx)+Math.abs(dy)>2)moved=true;
    yaw+=dx*0.01; pitch=Math.max(-1.1,Math.min(1.1,pitch+dy*0.01)); });
  canvas.addEventListener('pointerup',e=>{ dragging=false;
    if(!moved) handleClick(e); idle=0; });
  // mouse-wheel zoom (dolly the camera, clamped)
  canvas.addEventListener('wheel',e=>{ e.preventDefault();
    camera.position.z = Math.max(2.6, Math.min(8.5,
      camera.position.z + e.deltaY*0.0016));
    camera.lookAt(0,0,0); }, {passive:false});
  const ray=new THREE.Raycaster(), ndc=new THREE.Vector2();
  function handleClick(e){
    const b=canvas.getBoundingClientRect();
    ndc.x=((e.clientX-b.left)/b.width)*2-1; ndc.y=-((e.clientY-b.top)/b.height)*2+1;
    ray.setFromCamera(ndc,camera);
    if(!brain) return;
    const h=ray.intersectObject(brain,false); if(!h.length)return;
    const p=h[0].point.clone(); group.worldToLocal(p); p.normalize();
    const u=Math.atan2(p.z,p.x)/(2*Math.PI)+0.5;
    const vRaw=p.y*0.5+0.5; const t=mat.uniforms.uTime.value;
    let ax;
    if(st.pattern==='vertical') ax=((vRaw+t)%1+1)%1;
    else if(st.pattern==='spiral') ax=((u+vRaw*0.7+t)%1+1)%1;
    else ax=((u+t)%1+1)%1;
    openDetail(Math.min(activeCount-1, Math.floor(ax*activeCount)));
  }

  // ── shader material ───────────────────────────────────────────────
  let mat=null, brain=null;
  function makeMaterial(){
    return new THREE.ShaderMaterial({
      uniforms:{ uTex:{value:atlasTex}, uTime:{value:0}, uN:{value:activeCount},
        uBright:{value:st.bright}, uPattern:{value:PAT[st.pattern]||0},
        uBand:{value:st.band}, uRim:{value:st.rim}, uPulse:{value:1.0},
        uLegible:{value:(st.legible==null?0.55:st.legible)},
        uLights:{value:[ new THREE.Color(st.lightTL||'#000000'),
                         new THREE.Color(st.lightTR||'#000000'),
                         new THREE.Color(st.lightBL||'#000000'),
                         new THREE.Color(st.lightBR||'#000000') ]},
        uGold:{value:new THREE.Color(0xffcf72)} },
      vertexShader:`varying vec3 vObj; varying vec3 vNrm; varying vec3 vVN;
        void main(){ vObj=position; vNrm=normal; vVN=normalize(normalMatrix*normal);
          gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
      fragmentShader:`precision highp float;
        uniform sampler2D uTex; uniform float uTime,uN,uBright,uPattern,uBand,uRim,uPulse,uLegible;
        uniform vec3 uGold; uniform vec3 uLights[4];
        varying vec3 vObj; varying vec3 vNrm; varying vec3 vVN;
        #define PI 3.14159265
        void main(){
          vec3 p=normalize(vObj);
          float u=atan(p.z,p.x)/(2.0*PI)+0.5;
          float vRaw=p.y*0.5+0.5;
          float t=uTime;
          float ax, ay, band;
          float c=0.5, hw=uBand*0.5;
          if(uPattern<0.5){              // ribbon
            ax=fract(u+t);
            ay=clamp((vRaw-(c-hw))/(2.0*hw),0.0,1.0);
            band=smoothstep(c-hw-0.05,c-hw,vRaw)*(1.0-smoothstep(c+hw,c+hw+0.05,vRaw));
          } else if(uPattern<1.5){       // wrap (whole surface)
            ax=fract(u+t); ay=fract(vRaw*2.0); band=1.0;
          } else if(uPattern<2.5){       // spiral
            ax=fract(u+vRaw*0.7+t);
            ay=clamp((vRaw-(c-hw))/(2.0*hw),0.0,1.0);
            band=smoothstep(c-hw-0.05,c-hw,vRaw)*(1.0-smoothstep(c+hw,c+hw+0.05,vRaw));
          } else {                       // vertical
            ax=fract(u); ay=fract(vRaw+t); band=1.0;
          }
          vec3 art=texture2D(uTex,vec2(ax,ay)).rgb;
          art=pow(art,vec3(0.92))*uBright*uPulse;
          float lam=clamp(dot(normalize(vNrm),normalize(vec3(0.35,0.7,0.6))),0.0,1.0);
          vec3 cortex=vec3(0.16,0.115,0.075)*(0.45+0.75*lam);
          // legibility: 0 = art shaded by surface form, 1 = flat & bright.
          float shade=mix(0.5+0.6*lam, 1.18, uLegible);
          vec3 base=mix(cortex, art*shade, band);
          vec3 lit=base;
          // four screen-corner stage lights (view-space dirs; black = off)
          lit += base*uLights[0]*max(dot(vVN,normalize(vec3(-1.0, 1.0,0.8))),0.0)*1.5;
          lit += base*uLights[1]*max(dot(vVN,normalize(vec3( 1.0, 1.0,0.8))),0.0)*1.5;
          lit += base*uLights[2]*max(dot(vVN,normalize(vec3(-1.0,-1.0,0.8))),0.0)*1.5;
          lit += base*uLights[3]*max(dot(vVN,normalize(vec3( 1.0,-1.0,0.8))),0.0)*1.5;
          float fres=pow(1.0-clamp(vVN.z,0.0,1.0),2.2);
          lit += uGold*fres*uRim;
          gl_FragColor=vec4(lit,1.0);
        }`,
    });
  }

  // ── gear wiring ──────────────────────────────────────────────────
  const pop=root.querySelector('.cx-pop'), gear=root.querySelector('.cx-gear-trigger');
  if(gear&&pop){
    gear.addEventListener('click',e=>{ e.stopPropagation(); pop.hidden=!pop.hidden; });
    document.addEventListener('click',e=>{ if(pop.hidden)return;
      if(!pop.contains(e.target)&&e.target!==gear) pop.hidden=true; });
  }
  function setOut(fx,val){ const o=root.querySelector('[data-out="'+fx+'"]');
    if(o) o.textContent=val; }
  // initialize slider outputs
  function fmt(fx,v){ if(fx==='count')return v; if(fx==='speed')return (+v).toFixed(1);
    if(fx==='bright'||fx==='band')return (+v).toFixed(2);
    if(fx==='pulseRate')return (+v).toFixed(1);
    if(fx==='pulseAmt'||fx==='rim'||fx==='legible')return (+v).toFixed(2);
    return v; }
  root.querySelectorAll('.cx-fx-slider').forEach(sl=>{
    const fx=sl.dataset.fx; setOut(fx,fmt(fx,sl.value));
    sl.addEventListener('input',()=>{ const v=+sl.value; st[fx]=v; setOut(fx,fmt(fx,v));
      applySlider(fx,v); queueSave(fx,v); });
  });
  root.querySelectorAll('.cx-fx-btn').forEach(b=>{
    b.addEventListener('click',()=>{ const fx=b.dataset.fx, v=b.dataset.v;
      root.querySelectorAll('.cx-fx-btn[data-fx="'+fx+'"]').forEach(x=>x.classList.toggle('on',x===b));
      st[fx]=v; applySeg(fx,v); queueSave(fx,v); });
  });
  // corner-light color pickers → uLights[i]
  const LIGHT_IDX={lightTL:0, lightTR:1, lightBL:2, lightBR:3};
  root.querySelectorAll('.cx-fx-color').forEach(ci=>{
    ci.addEventListener('input',()=>{ const fx=ci.dataset.fx, v=ci.value;
      st[fx]=v;
      if(mat && fx in LIGHT_IDX) mat.uniforms.uLights.value[LIGHT_IDX[fx]].set(v);
      queueSave(fx,v); });
  });
  function applySlider(fx,v){
    if(!mat){ return; }
    if(fx==='count'){ rebuildAtlas(); }
    else if(fx==='bright') mat.uniforms.uBright.value=v;
    else if(fx==='band') mat.uniforms.uBand.value=v;
    else if(fx==='rim') mat.uniforms.uRim.value=v;
    else if(fx==='legible') mat.uniforms.uLegible.value=v;
    // speed/pulse* are read live in the loop
  }
  function applySeg(fx,v){
    if(fx==='order'){ rebuildAtlas(); }
    else if(fx==='pattern' && mat){ mat.uniforms.uPattern.value=PAT[v]||0; }
    // spin read live in the loop
  }

  // ── build + run ──────────────────────────────────────────────────
  (async function(){
    let geo;
    try{
      const mz=await parseMz3(meshUrl);
      geo=new THREE.BufferGeometry();
      geo.setAttribute('position',new THREE.BufferAttribute(mz.positions,3));
      if(mz.indices) geo.setIndex(new THREE.BufferAttribute(mz.indices,1));
      geo.rotateX(-Math.PI/2);
      geo.computeBoundingBox();
      const bb=geo.boundingBox, ctr=new THREE.Vector3(); bb.getCenter(ctr);
      geo.translate(-ctr.x,-ctr.y,-ctr.z);
      const sz=new THREE.Vector3(); bb.getSize(sz);
      const sc=3.1/Math.max(sz.x,sz.y,sz.z); geo.scale(sc,sc,sc);
      geo.computeVertexNormals();
    }catch(err){ return fail(err); }
    try{ images=await Promise.all(pool.map(c=>loadImg(c.art||c.image||''))); }
    catch(err){ return fail(err); }
    rebuildAtlas();
    mat=makeMaterial(); mat.uniforms.uN.value=activeCount;
    brain=new THREE.Mesh(geo,mat); group.add(brain);
    tick();
  })();
  function fail(err){ stage.innerHTML='<div style="padding:30px;color:#9d9582;'+
    'text-align:center;font-size:13px;line-height:1.6">Could not build the cortex.'+
    '<br><small>'+(err&&err.message||err)+'</small></div>'; }

  let last=performance.now();
  function tick(){
    const now=performance.now(); const dt=Math.min(0.05,(now-last)/1000); last=now;
    idle+=dt;
    if(mat){
      mat.uniforms.uTime.value += dt*st.speed*0.01;
      const pr=st.pulseRate, pa=st.pulseAmt;
      mat.uniforms.uPulse.value = pa>0 ? (1.0 + pa*0.6*Math.sin(now*0.001*pr*6.283)) : 1.0;
    }
    if(st.spin==='on' && !dragging && idle>0.4) yaw+=0.0035;
    group.rotation.y=yaw; group.rotation.x=pitch;
    renderer.render(scene,camera);
    requestAnimationFrame(tick);
  }
}
"""
