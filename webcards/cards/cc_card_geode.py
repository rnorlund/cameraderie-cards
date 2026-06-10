"""cc_card_geode.py — "Card Geode" dashboard art card.

Your collection as a geode: a rough rock cracked open to reveal a crystal-
lined hollow. Your most valuable cards are the polished gemstone facets
glinting in the cavity — sized by value, tinted by mana colour — ringed by
inward-pointing druzy crystal and concentric agate bands.

Two views the user toggles between, BOTH rendered up front so switching +
every setting (gem count, crystal palette, shimmer/spin) applies INSTANTLY
client-side with no page reload:
  • 2D — an SVG agate-slice cross-section (card art clipped into hex gems).
  • 3D — a procedural Three.js geode (no external model); card art is
    UV-mapped onto crystal faces.

A fixed POOL of cards is always rendered; the "gems" slider just shows/hides
within it, so nothing round-trips to the server to re-cut. Settings persist
via a debounced /set-pref (fire-and-forget) purely for the next page load.

Registered in cc_cards.py at module-load time.
"""
from __future__ import annotations

import html as _html
import json as _json
import math as _math

__all__ = ["render_card_geode_card", "CARD_GEODE_CATALOG_ENTRY"]


CARD_GEODE_CATALOG_ENTRY = {
    "key": "card_geode",
    "label": "💎 Card Geode",
    "desc": "Your collection cracked open like a geode — the most valuable "
            "cards are the gemstones lining the crystal cavity, sized by "
            "value and tinted by colour. 2D slice or 3D.",
    "type_line": "Visualization — Geode",
    "flavor": "Plain on the outside. Treasure within.",
    "default_w": 2, "default_h": 2, "min_w": 2, "min_h": 2,
}

# Max cards available to the card (the slider chooses the top 10..POOL). The
# 3D view maps these across crystal faces; the 2D slice caps its own gem count.
POOL = 250

_MANA_HUE = {
    "W": "#f5e3a0", "U": "#5b8fd6", "B": "#9a72ad", "R": "#d2493a",
    "G": "#48a85a", "M": "#e6c357", "C": "#cfd6cf",
}
_PALETTES = {
    "amethyst": "#9a72ad", "citrine": "#e6c357",
    "emerald": "#48a85a", "rose": "#d98aa6", "quartz": "#dfe4ea",
}

DEFAULT_SETTINGS = {
    "view": "2d",        # 2d | 3d
    "count": 24,         # top-N cards to feature (10..POOL); 3D packs ~6 per crystal
    "palette": "auto",   # auto | amethyst | citrine | emerald | rose | quartz
    "shimmer": "slow",   # off | slow | fast  (2D CSS shimmer / 3D sparkle+twinkle)
    "glow": "soft",      # dim | soft | bright (3D card-face glow)
    "spin": "on",        # 3d auto-orbit
}
_SETTING_KEYS = set(DEFAULT_SETTINGS)


def _color_bucket(colors) -> str:
    s = set((c or "").upper() for c in (colors or []))
    if not s:
        return "C"
    if len(s) >= 2:
        return "M"
    return next(iter(s))


def _select(all_items, n: int):
    by_name: dict[str, dict] = {}
    for r in all_items or []:
        if r.get("category") == "Sealed":
            continue
        name = (r.get("card_name") or r.get("matched") or r.get("card")
                or r.get("name") or "").strip()
        if not name:
            continue
        img = (r.get("image_normal") or r.get("image")
               or r.get("image_small") or "")
        if not img:
            continue
        unit = float(r.get("unit") or 0)
        total = unit * int(r.get("qty") or 1)
        if total <= 0:
            continue
        prev = by_name.get(name)
        if prev and total <= prev["_total"]:
            continue
        by_name[name] = {
            "name": name, "_total": total, "value": round(unit, 2),
            "image": img,
            "color": _color_bucket(r.get("color_identity") or r.get("colors")),
        }
    return sorted(by_name.values(), key=lambda c: -c["_total"])[:max(1, n)]


def _gem_hex(cx, cy, r, rot=0.0):
    return " ".join(
        f"{cx + r*_math.cos(rot + k*_math.pi/3):.1f},"
        f"{cy + r*_math.sin(rot + k*_math.pi/3):.1f}" for k in range(6))


def _build_2d_svg(cards, count: int) -> str:
    """The agate-slice SVG. Renders ALL pool gems (tagged with their index +
    auto hue); the slider toggles visibility client-side."""
    W, H = 400.0, 380.0
    cx, cy = W / 2, H / 2 + 6
    rx, ry = 150.0, 150.0

    def _blob(rxx, ryy, jitter, seed):
        m = 22
        pts = [(cx + rxx*(1 + jitter*_math.sin(seed + i*1.7)*_math.cos(seed*0.5 + i))*_math.cos(2*_math.pi*i/m),
                cy + ryy*(1 + jitter*_math.sin(seed + i*1.7)*_math.cos(seed*0.5 + i))*_math.sin(2*_math.pi*i/m))
               for i in range(m)]
        d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f} "
        for i in range(1, m + 1):
            d += f"L {pts[i % m][0]:.1f},{pts[i % m][1]:.1f} "
        return d + "Z"

    shell = []
    for i, (a, b, jit, fill) in enumerate([
            (rx+38, ry+38, 0.05, "url(#geo-rock)"), (rx+24, ry+24, 0.045, "#6b5536"),
            (rx+16, ry+16, 0.04, "#caa46a"), (rx+9, ry+9, 0.035, "#e9d6a8"),
            (rx+3, ry+3, 0.03, "#b9c7cc")]):
        shell.append(f'<path d="{_blob(a,b,jit,1.3+i)}" fill="{fill}" '
                     f'stroke="rgba(0,0,0,0.25)" stroke-width="1"/>')

    druzy = []
    m = 64
    for i in range(m):
        a = 2*_math.pi*i/m
        bx, by = cx + rx*_math.cos(a), cy + ry*_math.sin(a)
        ln = 10 + 9*abs(_math.sin(i*2.3))
        tx, ty = cx + (rx-ln)*_math.cos(a), cy + (ry-ln)*_math.sin(a)
        perp = a + _math.pi/2
        wx, wy = 3.0*_math.cos(perp), 3.0*_math.sin(perp)
        op = 0.30 + 0.45*abs(_math.sin(i*1.7))
        druzy.append(f'<polygon points="{bx-wx:.1f},{by-wy:.1f} {tx:.1f},{ty:.1f} '
                     f'{bx+wx:.1f},{by+wy:.1f}" fill="rgba(226,224,240,{op:.2f})" '
                     f'class="geo-druzy" style="--d:{(i%8)*0.18}s"/>')

    N = len(cards)
    GA = _math.pi * (3 - _math.sqrt(5))
    spread = min(rx, ry) * 0.80
    maxv = cards[0]["_total"] or 1.0
    defs, gems = [], []
    for i, c in enumerate(cards):
        rr = spread * _math.sqrt((i + 0.4) / N)
        a = i * GA
        gx, gy = cx + rr*_math.cos(a), cy + rr*_math.sin(a)*0.92
        vr = (c["_total"] / maxv) ** 0.5
        size = max(15, min(46, 20 + 30*vr*(1.0 - 0.35*i/max(1, N))))
        hue = _MANA_HUE.get(c["color"], "#cfd6cf")
        cid = f"geo-clip-{i}"
        poly = _gem_hex(gx, gy, size, (i*1.3) % (_math.pi/3))
        defs.append(f'<clipPath id="{cid}"><polygon points="{poly}"/></clipPath>')
        img = _html.escape(c["image"], quote=True)
        disp = "" if i < count else ' style="display:none"'
        gems.append(
            f'<g class="geo-gem" data-gi="{i}" data-hue="{hue}"{disp}>'
            f'<polygon class="geo-gem-tint" points="{poly}" fill="{hue}" opacity="0.9"/>'
            f'<image href="{img}" x="{gx-size:.1f}" y="{gy-size*1.2:.1f}" '
            f'width="{size*2:.1f}" height="{size*2.4:.1f}" '
            f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})" opacity="0.92"/>'
            f'<polygon points="{poly}" fill="url(#geo-facet)" clip-path="url(#{cid})"/>'
            f'<polygon class="geo-gem-rim" points="{poly}" fill="none" stroke="{hue}" '
            f'stroke-width="2.5" opacity="0.95"/>'
            f'<polygon points="{poly}" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="0.8"/>'
            f'<title>{_html.escape(c["name"])} · ${c["value"]:,.2f}</title></g>')

    sparks = []
    for i in range(10):
        a = i * GA
        rr = spread * 0.9 * ((i % 5) / 5.0)
        sx, sy = cx + rr*_math.cos(a), cy + rr*_math.sin(a)*0.9
        sparks.append(f'<circle class="geo-spark" cx="{sx:.1f}" cy="{sy:.1f}" r="1.6" '
                      f'style="--s:{(i*0.31)%2:.2f}s"/>')

    defs_block = "<defs>" + "".join(defs) + "</defs>" if defs else ""
    return f"""<svg viewBox="0 0 {int(W)} {int(H)}" class="geo-svg"
         preserveAspectRatio="xMidYMid meet" aria-label="Card geode">
      <defs>
        <radialGradient id="geo-rock" cx="50%" cy="42%" r="65%">
          <stop offset="0%" stop-color="#7a6647"/>
          <stop offset="60%" stop-color="#564636"/>
          <stop offset="100%" stop-color="#2c2418"/></radialGradient>
        <radialGradient id="geo-cavity" cx="50%" cy="50%" r="62%">
          <stop offset="0%" stop-color="#2a2140"/>
          <stop offset="60%" stop-color="#181226"/>
          <stop offset="100%" stop-color="#0a0712"/></radialGradient>
        <linearGradient id="geo-facet" x1="0" y1="0" x2="0.5" y2="1">
          <stop offset="0%" stop-color="rgba(255,255,255,0.55)"/>
          <stop offset="35%" stop-color="rgba(255,255,255,0.05)"/>
          <stop offset="100%" stop-color="rgba(0,0,0,0.35)"/></linearGradient>
      </defs>
      {''.join(shell)}
      <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#geo-cavity)"/>
      <g>{''.join(druzy)}</g>
      <g class="geo-gems">{defs_block}{''.join(gems)}</g>
      <g>{''.join(sparks)}</g>
    </svg>"""


def render_card_geode_card(ctx: dict, n: int | None = None) -> str:
    prefs_root = ctx.get("ui_prefs") or {}
    pane = (prefs_root.get("panes", {}) or {}).get("card_geode", {}) or {}
    settings = dict(DEFAULT_SETTINGS)
    for k in _SETTING_KEYS:
        if k in pane and pane[k] is not None:
            settings[k] = pane[k]
    try:
        settings["count"] = max(10, min(POOL, int(settings["count"])))
    except (TypeError, ValueError):
        settings["count"] = DEFAULT_SETTINGS["count"]

    cards = _select(ctx.get("all_items") or [], POOL)   # full pool; slider uses a prefix
    if len(cards) < 5:
        return ('<div class="card geode-card"><h3>💎 Card Geode</h3>'
                '<div class="hint" style="padding:18px;text-align:center;'
                'color:var(--muted)">Add a few priced cards with art and your '
                'collection will crystallize into a geode.</div></div>')

    # 2D slice caps its gem count (250 SVG hexes would be absurd); 3D uses all.
    svg2d = _build_2d_svg(cards[:40], min(settings["count"], 40))
    pool = [{"name": c["name"], "image": c["image"], "value": c["value"],
             "color": c["color"]} for c in cards]
    pool_json = _html.escape(_json.dumps(pool), quote=True)
    settings_json = _html.escape(_json.dumps(settings), quote=True)
    view = settings["view"]
    shimmer_dur = {"off": "0s", "slow": "5.5s", "fast": "2.6s"}.get(settings["shimmer"], "5.5s")
    shimmer_state = "paused" if settings["shimmer"] == "off" else "running"

    def _btn(fx, v, lbl, cur):
        on = " on" if str(cur) == v else ""
        return (f'<button class="geo-fx-btn{on}" data-fx="{fx}" data-v="{v}">{lbl}</button>')

    view_btns = _btn("view", "2d", "2D slice", view) + _btn("view", "3d", "3D", view)
    pal_btns = "".join(_btn("palette", k, lbl, settings["palette"]) for k, lbl in [
        ("auto", "auto"), ("amethyst", "amethyst"), ("citrine", "citrine"),
        ("emerald", "emerald"), ("rose", "rose"), ("quartz", "quartz")])
    shim_btns = "".join(_btn("shimmer", k, k, settings["shimmer"]) for k in ("off", "slow", "fast"))
    glow_btns = "".join(_btn("glow", k, k, settings.get("glow", "soft")) for k in ("dim", "soft", "bright"))
    spin_btns = "".join(_btn("spin", k, k, settings["spin"]) for k in ("on", "off"))

    return f"""
<div class="card geode-card" data-geode='{settings_json}' data-geode-cards='{pool_json}'
     style="--shimmer-dur:{shimmer_dur}; --shimmer-state:{shimmer_state}">
  <h3>💎 Card Geode</h3>
  <button class="card-gear geo-gear-trigger" type="button"
          aria-label="Geode settings" title="Geode settings">⚙</button>
  <div class="gear-pop geo-pop" hidden role="dialog" aria-label="Geode settings">
    <h4>Geode</h4>
    <div class="geo-fx-row"><span class="geo-fx-label">View</span>{view_btns}</div>
    <div class="geo-fx-row"><span class="geo-fx-label">Cards</span>
      <input class="geo-fx-slider" type="range" data-fx="count" min="10" max="{POOL}"
             step="5" value="{settings['count']}">
      <span class="geo-fx-out">{settings['count']}</span></div>
    <div class="geo-fx-row"><span class="geo-fx-label">Tint</span>{pal_btns}</div>
    <div class="geo-fx-row"><span class="geo-fx-label">Glow</span>{glow_btns}</div>
    <div class="geo-fx-row"><span class="geo-fx-label">Sparkle</span>{shim_btns}</div>
    <div class="geo-fx-row"><span class="geo-fx-label">Spin</span>{spin_btns}</div>
  </div>
  <div class="geo-2d geo-view"{' hidden' if view == '3d' else ''}>{svg2d}</div>
  <div class="geo-3d geo-view"{' hidden' if view == '2d' else ''}>
    <div class="geo3d-stage"><canvas class="geo3d-canvas"></canvas>
      <div class="geo3d-hint">drag · scroll to zoom · click a crystal</div>
      <div class="geo-cardview" hidden>
        <img class="geo-cardview-img" alt="">
        <div class="geo-cardview-cap"></div>
      </div></div>
  </div>
  {_GEODE_CSS}
  {_GEODE_CTRL_JS}
  {_GEODE_3D_JS}
</div>"""


_GEODE_CSS = """<style>
  .geode-card { position:relative; }
  .geo-view { width:100%; }
  .geo-svg { width:100%; height:auto; display:block; max-height:none !important; }
  .geo-gem { transform-box:fill-box; transform-origin:center;
      animation:geo-glint var(--shimmer-dur,5.5s) ease-in-out infinite;
      animation-delay:var(--gd,0s); animation-play-state:var(--shimmer-state,running); }
  @keyframes geo-glint { 0%,100% { filter:brightness(0.96); }
      50% { filter:brightness(1.18) drop-shadow(0 0 4px rgba(255,255,255,0.4)); } }
  .geo-druzy { animation:geo-twinkle var(--shimmer-dur,5.5s) ease-in-out infinite;
      animation-delay:var(--d,0s); animation-play-state:var(--shimmer-state,running); }
  @keyframes geo-twinkle { 0%,100% { opacity:0.45; } 50% { opacity:0.9; } }
  .geo-spark { fill:#fff; animation:geo-spk var(--shimmer-dur,5.5s) ease-in-out infinite;
      animation-delay:var(--s,0s); animation-play-state:var(--shimmer-state,running); }
  @keyframes geo-spk { 0%,100% { opacity:0; transform:scale(0.4);} 50% { opacity:0.95; transform:scale(1);} }
  .geo3d-stage { position:relative; width:100%; aspect-ratio:1/1; min-height:300px; }
  .geo3d-canvas { width:100% !important; height:100% !important; max-height:none !important;
      display:block; cursor:grab; position:absolute; inset:0; touch-action:none; }
  .geo3d-canvas:active { cursor:grabbing; }
  .geo3d-hint { position:absolute; left:50%; bottom:8px; transform:translateX(-50%);
      font-size:11px; color:var(--muted); opacity:0.7; pointer-events:none; }
  .geo-cardview { position:absolute; inset:0; display:flex; flex-direction:column;
      align-items:center; justify-content:center; gap:10px; cursor:pointer; z-index:4;
      background:radial-gradient(ellipse at center, rgba(10,7,18,0.82), rgba(10,7,18,0.96)); }
  .geo-cardview[hidden] { display:none; }
  .geo-cardview-img { max-height:82%; max-width:74%; border-radius:10px;
      box-shadow:0 0 0 1px rgba(212,175,55,0.55), 0 10px 40px rgba(0,0,0,0.7),
                 0 0 36px rgba(255,224,150,0.35);
      animation:geo-cardpop 0.34s cubic-bezier(.2,1.4,.4,1) both; }
  .geo-cardview-cap { font-size:13px; font-weight:700; color:#f4e6b8; text-align:center; padding:0 10px; }
  @keyframes geo-cardpop { 0% { transform:scale(0.6) rotate(-4deg); opacity:0; }
      100% { transform:scale(1) rotate(0); opacity:1; } }
  .geo-fx-row { display:flex; flex-wrap:wrap; gap:4px; align-items:center; margin-bottom:6px; }
  .geo-fx-label { font-size:11px; color:var(--muted); width:54px; }
  .geo-fx-btn { font:inherit; font-size:11px; padding:3px 8px; border-radius:6px; cursor:pointer;
      color:var(--text); background:#15151c; border:1px solid var(--line); }
  .geo-fx-btn.on { color:#2a1907; background:linear-gradient(180deg,#e6c780,#c8a247);
      border:0; font-weight:700; }
  .geo-fx-slider { flex:1; min-width:90px; }
  .geo-fx-out { font-size:12px; color:#e8dcb8; font-weight:700; width:22px; text-align:right; }
</style>"""


# Controller: handles the gear + all settings CLIENT-SIDE (no reload). It owns
# the 2D view directly and talks to the 3D view (if/when built) via events.
_GEODE_CTRL_JS = """<script>
(function(){
  function init(card){
    if(card._geoCtrl) return; card._geoCtrl=true;
    const PAL={amethyst:'#9a72ad',citrine:'#e6c357',emerald:'#48a85a',rose:'#d98aa6',quartz:'#dfe4ea'};
    let S={}; try{S=JSON.parse(card.getAttribute('data-geode'))||{};}catch(e){}
    const gear=card.querySelector('.geo-gear-trigger'), pop=card.querySelector('.geo-pop');
    const v2=card.querySelector('.geo-2d'), v3=card.querySelector('.geo-3d');
    if(gear&&pop){ gear.addEventListener('click',e=>{e.stopPropagation(); pop.hidden=!pop.hidden;});
      document.addEventListener('click',e=>{ if(pop.hidden)return;
        if(pop.contains(e.target)||e.target===gear)return; pop.hidden=true; }); }
    // debounced persist (no reload — purely for next page load)
    let saveT; const pending={};
    function save(k,v){ pending[k]=v; clearTimeout(saveT); saveT=setTimeout(()=>{
      const e=Object.entries(pending); for(const k in pending) delete pending[k];
      e.forEach(([key,value])=>{ try{ fetch('/set-pref',{method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({section:'card_geode',key,value})});}catch(_e){}}); },500); }

    function applyCount(n){
      v2 && v2.querySelectorAll('.geo-gem').forEach(g=>{
        g.style.display = (+g.dataset.gi < n) ? '' : 'none'; });
      card.dispatchEvent(new CustomEvent('geo:count',{detail:n}));
    }
    function applyPalette(p){
      v2 && v2.querySelectorAll('.geo-gem').forEach(g=>{
        const hue = PAL[p] || g.dataset.hue;
        const tint=g.querySelector('.geo-gem-tint'), rim=g.querySelector('.geo-gem-rim');
        if(tint) tint.setAttribute('fill',hue); if(rim) rim.setAttribute('stroke',hue);
      });
      card.dispatchEvent(new CustomEvent('geo:palette',{detail:p}));
    }
    function applyShimmer(s){
      const dur={off:'0s',slow:'5.5s',fast:'2.6s'}[s]||'5.5s';
      card.style.setProperty('--shimmer-dur',dur);
      card.style.setProperty('--shimmer-state', s==='off'?'paused':'running');
    }
    function applyView(view){
      if(view==='3d'){ if(v3) v3.hidden=false; if(v2) v2.hidden=true;
        card.dispatchEvent(new CustomEvent('geo:ensure3d')); }
      else { if(v2) v2.hidden=false; if(v3) v3.hidden=true; }
    }

    pop && pop.querySelectorAll('.geo-fx-btn').forEach(b=>{
      b.addEventListener('click',()=>{
        const fx=b.dataset.fx, val=b.dataset.v;
        pop.querySelectorAll('.geo-fx-btn[data-fx="'+fx+'"]').forEach(x=>x.classList.remove('on'));
        b.classList.add('on'); save(fx,val);
        if(fx==='view') applyView(val);
        else if(fx==='palette') applyPalette(val);
        else if(fx==='shimmer'){ applyShimmer(val);                 // 2D CSS
          card.dispatchEvent(new CustomEvent('geo:sparkle',{detail:val})); } // 3D twinkle+motes
        else if(fx==='glow') card.dispatchEvent(new CustomEvent('geo:glow',{detail:val}));
        else if(fx==='spin') card.dispatchEvent(new CustomEvent('geo:spin',{detail:val}));
      });
    });
    const sl=pop && pop.querySelector('.geo-fx-slider[data-fx="count"]');
    if(sl){ const out=sl.parentElement.querySelector('.geo-fx-out');
      sl.addEventListener('input',()=>{ if(out)out.textContent=sl.value; applyCount(+sl.value); });
      sl.addEventListener('change',()=>save('count',+sl.value)); }
  }
  document.querySelectorAll('.geode-card[data-geode]').forEach(init);
  document.addEventListener('cc-rerender',()=>
    document.querySelectorAll('.geode-card[data-geode]').forEach(init));
})();
</script>"""


# 3D view: real quartz crystals — an F-sided prism that tapers to a point,
# with ONE card UV-mapped to each side face + a translucent crystal tip.
# Several crystals of varied length/size/orientation; a slow spin reveals all
# faces; shimmer pulses the crystal tips. Builds lazily on 'geo:ensure3d'.
_GEODE_3D_JS = """<script type="module">
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const cards = document.querySelectorAll('.geode-card[data-geode-cards]');
const root = cards[cards.length - 1];
if (root && !root.__geo3dBound) {
  root.__geo3dBound = true;
  let pool=[], S={};
  try{ pool=JSON.parse(root.getAttribute('data-geode-cards'))||[]; }catch(e){}
  try{ S=JSON.parse(root.getAttribute('data-geode'))||{}; }catch(e){}
  const HUE={W:0xf5e3a0,U:0x5b8fd6,B:0x9a72ad,R:0xd2493a,G:0x48a85a,M:0xe6c357,C:0xcfd6cf};
  const PAL={amethyst:0x9a72ad,citrine:0xe6c357,emerald:0x48a85a,rose:0xd98aa6,quartz:0xdfe4ea};
  const FACES=6;                 // hexagonal quartz → 6 side faces = 6 cards
  let built=false, group=null, crystalGroup=null, renderer=null, scene=null, camera=null;
  let spinOn=(S.spin||'on')==='on', countN=+S.count||9, paletteV=S.palette||'auto';
  let glowV=S.glow||'soft', sparkleV=S.shimmer||'slow';
  let pulseMats=[], glintMats=[], motes=null;
  let druzyGeo=null, druzyMat=null;   // shared geo/mat for the inner-wall carpet
  const loader=new THREE.TextureLoader(); loader.crossOrigin='anonymous';
  function proxied(u){ if(!u)return u; if(location.protocol==='file:')return u;
    if(u.indexOf('https://cards.scryfall.io/')===0) return '/scryfall-img?url='+encodeURIComponent(u); return u; }
  function rand(s){ const x=Math.sin(s*127.1+311.7)*43758.5453; return x-Math.floor(x); }
  // sharper card text: bigger Scryfall image at low card counts (few textures),
  // smaller when there are many on screen; + anisotropic filtering at angles.
  function texSize(n){ return n<=24?'large':(n<=80?'normal':'small'); }
  function loadTex(url,size){
    const u=(url||'').replace('/normal/','/'+size+'/');
    const t=loader.load(proxied(u)); t.colorSpace=THREE.SRGBColorSpace;
    if(renderer){ try{ t.anisotropy=renderer.capabilities.getMaxAnisotropy(); }catch(_e){} }
    t.magFilter=THREE.LinearFilter; t.minFilter=THREE.LinearMipmapLinearFilter;
    return t;
  }
  // 4-point star sprite for the sparkle motes (instead of square points)
  let _sparkTex=null;
  function sparkTex(){
    if(_sparkTex) return _sparkTex;
    const c=document.createElement('canvas'); c.width=c.height=64; const x=c.getContext('2d');
    x.translate(32,32);
    x.fillStyle='rgba(255,250,228,0.95)';
    for(let i=0;i<4;i++){ x.rotate(Math.PI/2);
      x.beginPath(); x.moveTo(0,-30); x.lineTo(3.5,-4); x.lineTo(0,0); x.lineTo(-3.5,-4);
      x.closePath(); x.fill(); }
    const g=x.createRadialGradient(0,0,0,0,0,9);
    g.addColorStop(0,'rgba(255,255,255,1)'); g.addColorStop(1,'rgba(255,245,210,0)');
    x.fillStyle=g; x.beginPath(); x.arc(0,0,9,0,7); x.fill();
    _sparkTex=new THREE.CanvasTexture(c); return _sparkTex;
  }

  // One crystal: F-sided prism tapering to an apex. Each side face is its own
  // material group (a card); the F tip triangles share a translucent tip mat.
  function makeCrystal(F, rad, bodyH, tipH, texes, tint, seed){
    const pos=[],uv=[],idx=[]; const geo=new THREE.BufferGeometry();
    const apex=[0,bodyH+tipH,0]; let v=0,ic=0;
    // Each face is a PENTAGON (rect body + triangular tip). Map the card
    // continuously up the whole pentagon: body shows v 0..fb, the tip
    // continues v fb..1 to the point. A few tips are left as clear crystal.
    const fb=bodyH/(bodyH+tipH);
    for(let k=0;k<F;k++){
      const a0=k/F*Math.PI*2, a1=(k+1)/F*Math.PI*2;
      const b0=[rad*Math.cos(a0),0,rad*Math.sin(a0)], b1=[rad*Math.cos(a1),0,rad*Math.sin(a1)];
      const t0=[rad*Math.cos(a0),bodyH,rad*Math.sin(a0)], t1=[rad*Math.cos(a1),bodyH,rad*Math.sin(a1)];
      pos.push(b0[0],b0[1],b0[2], b1[0],b1[1],b1[2], t1[0],t1[1],t1[2], t0[0],t0[1],t0[2]);
      uv.push(0,0, 1,0, 1,fb, 0,fb);
      idx.push(v,v+1,v+2, v,v+2,v+3); geo.addGroup(ic,6,k); ic+=6; v+=4;
      pos.push(t0[0],t0[1],t0[2], t1[0],t1[1],t1[2], apex[0],apex[1],apex[2]);
      uv.push(0,fb, 1,fb, 0.5,1);
      // most tips continue their face's card; ~1-in-5 stays clear crystal
      const tipMapped = texes[k] && rand(seed*13 + k + 1) < 0.78;
      idx.push(v,v+1,v+2); geo.addGroup(ic,3, tipMapped ? k : F); ic+=3; v+=3;
    }
    geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
    geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
    geo.setIndex(idx); geo.computeVertexNormals();
    const mats=[];
    for(let k=0;k<F;k++){
      const tex=texes[k];
      if(tex){
        // card face: crisp art (Standard, no clearcoat haze → sharper text +
        // lighter at high counts). DoubleSide so the card shows from inside too.
        const cardMat=new THREE.MeshStandardMaterial({map:tex, emissiveMap:tex, emissive:0xffffff,
          emissiveIntensity:0.2, roughness:0.34, metalness:0.18, envMapIntensity:1.1,
          side:THREE.DoubleSide});
        cardMat.userData.ph=rand(seed*7+k+3)*6.283;   // twinkle phase
        glintMats.push(cardMat); mats.push(cardMat); }
      else { const m=new THREE.MeshPhysicalMaterial({color:tint, roughness:0.08, metalness:0.2,
          transmission:0.5, ior:1.6, thickness:0.5, transparent:true, opacity:0.85,
          clearcoat:1.0, envMapIntensity:1.4, flatShading:true,
          side:THREE.DoubleSide}); pulseMats.push(m); mats.push(m); }
    }
    // crystal tip: glassy translucent point (double-sided too)
    const tipM=new THREE.MeshPhysicalMaterial({color:tint, roughness:0.05, metalness:0.1,
      transmission:0.7, ior:1.6, thickness:0.6, transparent:true, opacity:0.8,
      clearcoat:1.0, envMapIntensity:1.5, emissive:tint, emissiveIntensity:0.22,
      flatShading:true, side:THREE.DoubleSide});
    pulseMats.push(tipM); mats.push(tipM);
    return new THREE.Mesh(geo,mats);
  }

  // Cavity: a hollow sphere. Crystals GROW INWARD from its inner wall toward
  // the centre (how a real geode is structured) — the whole back+side wall is
  // carpeted in small druzy crystals, with a few bigger card-crystal clusters.
  const CC=new THREE.Vector3(0,0,-0.7), CR=1.85;   // cavity centre + radius
  const UP=new THREE.Vector3(0,1,0), GA=Math.PI*(3-Math.sqrt(5));
  // outward surface normal on the back+side wall (skip the front opening)
  function wallNormal(vv, ph){
    const z=-1+1.35*vv;                            // -1 back pole .. 0.35 toward rim
    const r2=Math.sqrt(Math.max(0,1-z*z));
    return new THREE.Vector3(r2*Math.cos(ph), r2*Math.sin(ph), z);
  }
  function buildCrystals(n){
    if(!crystalGroup) return;
    while(crystalGroup.children.length){ const m=crystalGroup.children.pop();
      if(m.userData && m.userData.unique && m.geometry) m.geometry.dispose(); }
    pulseMats=[]; glintMats=[];
    if(!druzyGeo) druzyGeo=new THREE.ConeGeometry(1,1,5);
    if(!druzyMat) druzyMat=new THREE.MeshPhysicalMaterial({color:0xe7e2f4,roughness:0.1,
      metalness:0.05,transmission:0.4,ior:1.5,thickness:0.4,transparent:true,opacity:0.85,
      clearcoat:1.0,envMapIntensity:1.5,flatShading:true,side:THREE.DoubleSide});

    // ── carpet the entire inner wall with small inward druzy crystals ──
    for(let i=0;i<150;i++){
      const nrm=wallNormal(rand(i*2+1), i*GA);
      const drad=0.05+rand(i*2+2)*0.05, dlen=0.18+rand(i*3+1)*0.42;
      const m=new THREE.Mesh(druzyGeo,druzyMat); m.scale.set(drad,dlen,drad);
      m.quaternion.setFromUnitVectors(UP, nrm.clone().negate());     // apex points inward
      m.position.copy(CC).addScaledVector(nrm, CR - dlen*0.5);       // base on the wall
      crystalGroup.add(m);
    }
    // ── card-crystals on the wall, growing inward; the chosen top-N cards
    //    are packed ~FACES per crystal ──
    const nCards=Math.max(6,Math.min(pool.length,(n|0)||24));
    const sz=texSize(nCards);
    const nBig=Math.max(2,Math.min(45,Math.ceil(nCards/FACES)));
    let ci=0;
    for(let c=0;c<nBig;c++){
      const texes=[], faceCards=[]; let fcol='C';
      for(let f=0;f<FACES;f++){ const card=pool[ci % nCards]; ci++;
        texes.push(loadTex(card.image, sz)); faceCards.push(card); if(f===0) fcol=card.color; }
      const tint=(paletteV&&PAL[paletteV]) || HUE[fcol] || 0x9a72ad;
      const rad=0.24+rand(c*3+1)*0.16;
      const bodyH=rad*(1.6+rand(c*3+2)*1.4);        // varied lengths
      const tipH=rad*(1.1+rand(c*3+3)*0.9);
      const cm=makeCrystal(FACES,rad,bodyH,tipH,texes,tint,c+1);
      cm.userData.unique=true; cm.userData.cards=faceCards;   // for click-to-view
      // spread over the back+lower wall (golden-angle), cluster slightly
      const nrm=wallNormal(0.12+rand(c*5+1)*0.72, c*GA+0.3);
      cm.quaternion.setFromUnitVectors(UP, nrm.clone().negate());
      cm.position.copy(CC).addScaledVector(nrm, CR);                 // base on the wall
      crystalGroup.add(cm);
    }
  }

  function build(){
    if(built) return; built=true;
    const stage=root.querySelector('.geo3d-stage'), canvas=root.querySelector('.geo3d-canvas');
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
    renderer.setPixelRatio(Math.min(devicePixelRatio,2));
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    scene=new THREE.Scene();
    // a small gradient environment so the crystals actually reflect/refract
    // light → that glassy "shiny crystal" look (clearcoat + transmission need it)
    { const cnv=document.createElement('canvas'); cnv.width=16; cnv.height=64;
      const cx=cnv.getContext('2d'); const g=cx.createLinearGradient(0,0,0,64);
      g.addColorStop(0,'#fff6da'); g.addColorStop(0.45,'#6a5a86'); g.addColorStop(1,'#0a0712');
      cx.fillStyle=g; cx.fillRect(0,0,16,64);
      const et=new THREE.CanvasTexture(cnv); et.mapping=THREE.EquirectangularReflectionMapping;
      const pm=new THREE.PMREMGenerator(renderer);
      scene.environment=pm.fromEquirectangular(et).texture; et.dispose(); pm.dispose(); }
    camera=new THREE.PerspectiveCamera(44,1,0.1,100);
    camera.position.set(0,0.3,4.7); camera.lookAt(0,0,-0.3);
    group=new THREE.Group(); scene.add(group);
    crystalGroup=new THREE.Group(); group.add(crystalGroup);

    // ── rock geode shell: the cluster sits in a rough rocky cavity ──
    function noise3(x,y,z){ return Math.sin(x*3.1+y*1.7)*0.5+Math.sin(y*2.3+z*2.9)*0.3+Math.sin(z*3.7+x*1.1)*0.2; }
    // dark rocky bowl behind the cluster (we look INTO it; opening → camera)
    const bowlGeo=new THREE.SphereGeometry(2.15,64,44,0,Math.PI*2,0,Math.PI*0.60);
    { const p=bowlGeo.attributes.position,vv=new THREE.Vector3();
      for(let i=0;i<p.count;i++){ vv.fromBufferAttribute(p,i);
        vv.multiplyScalar(1+0.13*noise3(vv.x,vv.y,vv.z)); p.setXYZ(i,vv.x,vv.y,vv.z);} bowlGeo.computeVertexNormals(); }
    const bowl=new THREE.Mesh(bowlGeo,new THREE.MeshStandardMaterial(
        {color:0x2c2317,roughness:1,metalness:0,side:THREE.BackSide,flatShading:true}));
    bowl.rotation.x=-Math.PI/2; bowl.position.z=-0.7; group.add(bowl);
    // craggy rock rim around the opening (the geode's stony edge)
    const rrimGeo=new THREE.TorusGeometry(1.98,0.5,16,72);
    { const p=rrimGeo.attributes.position,vv=new THREE.Vector3(),nn=new THREE.Vector3();
      for(let i=0;i<p.count;i++){ vv.fromBufferAttribute(p,i); nn.copy(vv).normalize();
        vv.addScaledVector(nn,0.26*noise3(vv.x*0.9,vv.y*0.9,vv.z*0.9)); p.setXYZ(i,vv.x,vv.y,vv.z);} rrimGeo.computeVertexNormals(); }
    const rrim=new THREE.Mesh(rrimGeo,new THREE.MeshStandardMaterial(
        {color:0xc3bdb0,roughness:1,metalness:0,flatShading:true}));   // pale grey/white rind
    rrim.position.z=-0.25; group.add(rrim);
    // thin white chalcedony band just inside the rock (the pale ring real
    // store geodes have between the grey rind and the crystals)
    const aband=new THREE.Mesh(new THREE.TorusGeometry(1.62,0.1,12,72),
        new THREE.MeshStandardMaterial({color:0xe8e3d6,roughness:0.55,metalness:0.1,envMapIntensity:1.0}));
    aband.position.z=-0.05; group.add(aband);

    scene.add(new THREE.AmbientLight(0xffffff,0.55));
    const key=new THREE.DirectionalLight(0xfff3e0,1.0); key.position.set(2.5,3,4); scene.add(key);
    const rimL=new THREE.DirectionalLight(0xa9c0ff,0.7); rimL.position.set(-3,1,-2); scene.add(rimL);
    const spark=new THREE.PointLight(0xffffff,0,10); scene.add(spark);
    // internal light: glows the crystals from the hollow centre (pulsable)
    const inner=new THREE.PointLight(0xffe8c0,0.6,8); inner.position.copy(CC); inner.position.z+=0.3; scene.add(inner);
    let lw=0,lh=0;
    function resize(){ const w=stage.clientWidth|0,h=stage.clientHeight|0;
      if(w<2||h<2||(w===lw&&h===lh))return; lw=w;lh=h;
      renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix(); }
    resize(); window.addEventListener('resize',resize);
    if(window.ResizeObserver) new ResizeObserver(resize).observe(stage);

    buildCrystals(countN);

    // floating sparkle motes drifting in the cavity (a bit of life)
    { const N=60, pts=new Float32Array(N*3);
      for(let i=0;i<N;i++){ const r=0.3+Math.random()*1.45, a=Math.random()*6.283;
        pts[i*3]=Math.cos(a)*r*0.75; pts[i*3+1]=(Math.random()-0.5)*2.4;
        pts[i*3+2]=CC.z+0.4+Math.sin(a)*r*0.55; }
      const pg=new THREE.BufferGeometry(); pg.setAttribute('position',new THREE.BufferAttribute(pts,3));
      motes=new THREE.Points(pg,new THREE.PointsMaterial({map:sparkTex(),color:0xfff3d0,
        size:0.17,transparent:true,opacity:0.0,depthWrite:false,blending:THREE.AdditiveBlending}));
      group.add(motes); }

    // ── orbit + zoom: move the CAMERA around the geode (rock + crystals stay
    //    rigidly one solid object). Drag = orbit, wheel = zoom. ──
    const TGT=new THREE.Vector3(0,0,-0.3);
    let baseAz=0, basePol=0.16, dist=4.7, dragging=false, px=0, py=0;
    function applyCam(az,pol){
      const cp=Math.cos(pol);
      camera.position.set(TGT.x+dist*cp*Math.sin(az), TGT.y+dist*Math.sin(pol),
                          TGT.z+dist*cp*Math.cos(az));
      camera.lookAt(TGT);
    }
    // click a crystal → lightbox that card (raycast; ignored if it was a drag)
    const ray=new THREE.Raycaster(), ndc=new THREE.Vector2();
    const cardview=root.querySelector('.geo-cardview');
    const cvImg=cardview&&cardview.querySelector('.geo-cardview-img');
    const cvCap=cardview&&cardview.querySelector('.geo-cardview-cap');
    if(cardview) cardview.addEventListener('click',()=>{ cardview.hidden=true; });
    function pickCard(e){
      const r=canvas.getBoundingClientRect();
      ndc.x=((e.clientX-r.left)/r.width)*2-1; ndc.y=-((e.clientY-r.top)/r.height)*2+1;
      ray.setFromCamera(ndc,camera);
      const hits=ray.intersectObjects(crystalGroup.children,false);
      for(let i=0;i<hits.length;i++){ const cs=hits[i].object.userData.cards;
        if(cs&&cs.length) return cs[Math.floor((hits[i].faceIndex||0)/3)%cs.length]; }
      return null;
    }
    let moved=0;
    canvas.addEventListener('pointerdown',e=>{dragging=true;px=e.clientX;py=e.clientY;moved=0;try{canvas.setPointerCapture(e.pointerId);}catch(_e){}});
    canvas.addEventListener('pointermove',e=>{ if(!dragging)return;
      moved+=Math.abs(e.clientX-px)+Math.abs(e.clientY-py);
      baseAz -= (e.clientX-px)*0.008; basePol += (e.clientY-py)*0.008;
      basePol=Math.max(-1.25,Math.min(1.25,basePol)); px=e.clientX; py=e.clientY; });
    canvas.addEventListener('pointerup',e=>{ dragging=false;
      if(moved<6 && cardview && cvImg){ const card=pickCard(e);
        if(card){ cvImg.src=(card.image||'').replace('/normal/','/large/');
          cvCap.textContent=card.name+(card.value?(' · $'+(+card.value).toFixed(2)):'');
          cardview.hidden=false; } } });
    canvas.addEventListener('pointerleave',()=>dragging=false);
    canvas.addEventListener('wheel',e=>{ e.preventDefault();
      dist*=(1 + (e.deltaY>0?0.09:-0.09)); dist=Math.max(2.2,Math.min(9.0,dist)); },{passive:false});
    let t=0, intro=0;   // intro: crystal grow-in + sparkle burst on appear
    (function tick(){ t+=0.016;
      // crystal-themed appear: the cluster grows in from the wall + motes burst
      if(intro<1){ intro=Math.min(1,intro+0.02); const e=1-Math.pow(1-intro,3);
        crystalGroup.scale.setScalar(0.32+0.68*e); }
      // idle: a gentle orbit ADDED to the user's dragged view (so releasing
      // doesn't snap). The geode itself never moves — only the camera.
      const wob = (spinOn&&!dragging) ? 0.45*Math.sin(t*0.3) : 0;
      const wobP = (spinOn&&!dragging) ? 0.05*Math.sin(t*0.24) : 0;
      applyCam(baseAz+wob, basePol+wobP);
      // sweeping key light glints across the facets
      spark.position.set(Math.cos(t*0.9)*3.4, 1.6+Math.sin(t*0.7)*1.4, Math.sin(t*0.9)*3.4+2.2);
      spark.intensity=0.6+0.5*Math.sin(t*2.2);
      // glow (base face brightness) + sparkle (per-crystal twinkle + motes)
      const GB={dim:0.06,soft:0.2,bright:0.46}[glowV] ?? 0.2;
      const SP={off:[0,0],slow:[1.7,0.13],fast:[3.4,0.22]}[sparkleV] || [1.7,0.13];
      for(let i=0;i<glintMats.length;i++){ const m=glintMats[i];
        m.emissiveIntensity=GB + SP[1]*Math.sin(t*SP[0]+m.userData.ph); }
      const tp=Math.max(0, GB*0.8+0.18 + SP[1]*1.3*Math.sin(t*SP[0]*0.85));
      for(let i=0;i<pulseMats.length;i++) pulseMats[i].emissiveIntensity=tp;
      // internal light: base from Glow, pulse from Sparkle
      inner.intensity=Math.max(0, 0.5 + GB*3.2 + SP[1]*4.0*Math.sin(t*SP[0]*0.9));
      if(motes){ motes.rotation.y += 0.0012*((SP[0]||0.5)+0.4);
        const burst = intro<1 ? 0.85*(1-intro) : 0;       // sparkle burst on appear
        motes.material.opacity = burst + ((sparkleV==='off') ? 0.0 : (0.3+0.28*Math.sin(t*2.0))); }
      renderer.render(scene,camera); requestAnimationFrame(tick); })();
  }

  root.addEventListener('geo:ensure3d',build);
  root.addEventListener('geo:count',e=>{ countN=e.detail; buildCrystals(countN); });
  root.addEventListener('geo:palette',e=>{ paletteV=e.detail; buildCrystals(countN); });
  root.addEventListener('geo:glow',e=>{ glowV=e.detail; });
  root.addEventListener('geo:sparkle',e=>{ sparkleV=e.detail; });
  root.addEventListener('geo:spin',e=>{ spinOn=(e.detail==='on'); });
  if((S.view||'2d')==='3d') build();
}
</script>"""
