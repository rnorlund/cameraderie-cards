"""
cc_card_of_cards.py — "Card-of-Cards Mosaic" dashboard widget.

A giant card silhouette (e.g. Sol Ring, Black Lotus) rendered as a
mosaic of hundreds of TINY card-art tiles drawn from the user's
collection. Each cell of the giant card matches its target color
to the best-matching owned card by average tile color, so the
silhouette reads as the subject while every pixel is genuinely a
piece of the user's binder.

Cross-origin: Scryfall JPGs aren't CORS-clean, but we already have
a same-origin proxy at /scryfall-img?url=... (whitelisted to
https://cards.scryfall.io/). Loading both the subject + tile images
via the proxy gives us a clean canvas we can read with getImageData
for average-color matching.

Settings (per-instance, localStorage):
  subject     "top" / "random" — pick the silhouette card
  resolution  16 / 24 / 36 — grid resolution (columns; rows scale
              with card aspect 488/680)
  tilekind    "card" / "square" — tile rendering style
  reveal      "instant" / "build" — render all at once vs cell-by-cell
"""
from __future__ import annotations

import html as _html
import json as _json
import random as _random

import cc_cards as _cc

__all__ = ["render_card_of_cards_card", "CARD_OF_CARDS_CATALOG_ENTRY"]


CARD_OF_CARDS_CATALOG_ENTRY = {
    "key": "card_of_cards",
    "label": "🎴 Card-of-Cards Mosaic",
    "desc": "A giant card silhouette woven from hundreds of your own "
            "card-art tiles. Picks a new subject daily.",
    "type_line": "Visualization — Mosaic",
    "flavor": "Every card you own is a brushstroke.",
    "default_w": 2, "default_h": 2, "min_w": 2, "min_h": 2,
}


def _pick_subjects(all_items: list[dict]) -> list[dict]:
    """ALL owned cards with Scryfall images, sorted by value descending.
    No cap — the JS picker uses the full list so "random" really
    samples from the whole collection (and the top-N for "top value"
    can vary across clicks instead of always returning the same #1).
    Pricy cards come first so the JS can slice the top-N easily."""
    pool: list[tuple[float, dict]] = []
    for r in all_items or []:
        if r.get("category") == "Sealed":
            continue
        img = (r.get("image_normal") or r.get("image")
               or r.get("image_small") or "")
        if not img or "cards.scryfall.io" not in img:
            continue
        v = float(r.get("total") or 0.0) or float(r.get("unit") or 0.0)
        if v <= 0:
            continue
        pool.append((v, {
            "name":  r.get("matched") or r.get("card") or r.get("name") or "?",
            "image": img,
            "value": round(v, 2),
        }))
    pool.sort(key=lambda x: -x[0])
    return [c for _, c in pool]


def _pick_tiles(all_items: list[dict], n: int = 60) -> list[dict]:
    """Owned cards to use as mosaic tiles. We want variety + enough
    cards to color-match each cell, so pull more than the typical
    top-N. Mix Singles + Graded; skip Sealed."""
    pool: list[tuple[float, dict]] = []
    for r in all_items or []:
        if r.get("category") == "Sealed":
            continue
        img = (r.get("image_small") or r.get("image")
               or r.get("image_normal") or "")
        if not img or "cards.scryfall.io" not in img:
            continue
        v = float(r.get("total") or 0.0) or float(r.get("unit") or 0.0)
        # We DON'T filter by value — even cheap cards make good
        # mosaic pixels if they have art with varied color.
        name = r.get("matched") or r.get("card") or r.get("name") or ""
        if not name:
            continue
        pool.append((v, {
            "name":  name,
            "image": img,
            "value": round(v, 2),
        }))
    pool.sort(key=lambda x: -x[0])
    return [c for _, c in pool[:max(1, int(n))]]


def render_card_of_cards_card(ctx: dict) -> str:
    all_items = ctx.get("all_items") or []
    subjects = _pick_subjects(all_items)
    # Send the full top-300 tile pool. The JS-side slider picks how
    # many to actually use when weaving the mosaic (default 80).
    tiles    = _pick_tiles(all_items, n=300)
    if not subjects or len(tiles) < 8:
        return (
            '<div class="card coc-card">'
            '<h3>🎴 Card-of-Cards Mosaic</h3>'
            '<div class="hint" style="padding:18px 0;text-align:center;'
            'color:var(--muted);">Need at least 8 priced cards with '
            'Scryfall images to weave the mosaic.</div></div>'
        )
    subjects_json = _html.escape(_json.dumps(subjects), quote=True)
    tiles_json    = _html.escape(_json.dumps(tiles), quote=True)
    return f"""
<div class="card coc-card">
  <h3>🎴 Card-of-Cards Mosaic</h3>
  <button class="card-gear coc-gear-trigger" type="button"
          aria-label="Mosaic settings" title="Mosaic settings">⚙</button>
  <div class="gear-pop coc-pop" hidden role="dialog"
       aria-label="Mosaic settings">
    <h4>Mosaic</h4>
    <div class="coc-fx-row">
      <span class="coc-fx-label">Subject pool</span>
      <button class="coc-fx-btn" data-fx="subject" data-v="top">top value</button>
      <button class="coc-fx-btn" data-fx="subject" data-v="random">random</button>
    </div>
    <p class="coc-fx-hint">Pool used when picking the NEXT card —
       <em>top value</em> samples your 15 most valuable; <em>random</em>
       samples your whole collection. Click <strong>New Card</strong>
       below or the › arrow to apply.</p>
    <div class="coc-fx-row">
      <span class="coc-fx-label">Tile pool</span>
      <input class="coc-fx-slider" type="range" data-fx="tilepool"
             min="20" max="300" step="10" value="80">
      <span class="coc-fx-out" data-out="tilepool">80</span>
    </div>
    <p class="coc-fx-hint">How many of your top cards (by value) feed the
       mosaic palette. More = more colour variety + finer matching.</p>
    <div class="coc-fx-row">
      <span class="coc-fx-label">Resolution</span>
      <button class="coc-fx-btn" data-fx="resolution" data-v="16">low</button>
      <button class="coc-fx-btn" data-fx="resolution" data-v="24">medium</button>
      <button class="coc-fx-btn" data-fx="resolution" data-v="36">high</button>
    </div>
    <div class="coc-fx-row">
      <span class="coc-fx-label">Tile shape</span>
      <button class="coc-fx-btn" data-fx="tilekind" data-v="card">card</button>
      <button class="coc-fx-btn" data-fx="tilekind" data-v="square">square</button>
    </div>
    <div class="coc-fx-row">
      <span class="coc-fx-label">Reveal</span>
      <button class="coc-fx-btn" data-fx="reveal" data-v="instant">instant</button>
      <button class="coc-fx-btn" data-fx="reveal" data-v="build">build-up</button>
    </div>
    <div class="coc-fx-row">
      <span class="coc-fx-label">&nbsp;</span>
      <button class="coc-fx-btn coc-fx-newcard" data-coc-regen="1">
        ↻ New Card
      </button>
    </div>
  </div>
  <div class="coc-stage" data-coc-subjects='{subjects_json}'
                          data-coc-tiles='{tiles_json}'>
    <canvas class="coc-canvas" width="600" height="800"></canvas>
    <div class="coc-status">Loading mosaic…</div>
    <div class="coc-label"><span class="coc-current"></span></div>
    <!-- Guess-the-card puzzle. Hidden by default; shown when
         settings.puzzle = 'on'. 4 buttons (1 correct + 3 distractors
         drawn from the user's other top cards), plus ↻ swap and
         👁 reveal in the action row. Semi-transparent so it sits
         over the mosaic without hiding too much of it. -->
    <div class="coc-puzzle" hidden>
      <button class="coc-puzzle-close" type="button"
              title="Close puzzle (turn off in settings to bring back)"
              aria-label="Close puzzle">×</button>
      <div class="coc-puzzle-q">🎴 Which card is this?</div>
      <div class="coc-puzzle-opts"></div>
      <div class="coc-puzzle-result"></div>
      <div class="coc-puzzle-actions">
        <button class="coc-puzzle-swap" type="button">↻ swap</button>
        <button class="coc-puzzle-reveal" type="button">👁 reveal</button>
      </div>
    </div>
    <!-- Reveal overlay: the actual subject card art fades IN over
         the mosaic when the user wins or hits 👁 reveal. Hidden
         by default; opacity-animates from 0 → 1. -->
    <img class="coc-reveal-img" alt="" hidden>
    <!-- Prev/Next navigation arrows on the LEFT and RIGHT edges of
         the stage. Always visible. Prev is disabled until there's
         history to step back into; next always picks a new subject
         (respecting the current "subject" setting). -->
    <button class="coc-nav coc-nav-prev" type="button"
            aria-label="Previous subject" title="Previous subject"
            disabled>‹</button>
    <button class="coc-nav coc-nav-next" type="button"
            aria-label="Next subject" title="Next subject">›</button>
  </div>
  <!-- Footer-level puzzle toggle — pinned to the card's bottom-right
       so it sits at the same level as the framework's flavor text
       ("Every card you own is a brushstroke."). Easy reach without
       opening the gear popover. -->
  <button class="coc-puzzle-toggle" type="button"
          aria-label="Toggle guess-the-card puzzle">
    <span class="coc-puzzle-toggle-icon">🎴</span>
    <span class="coc-puzzle-toggle-label">Guess the card</span>
  </button>
  {_COC_CSS}
  <script>{_COC_JS}</script>
</div>
"""


_COC_CSS = """
<style>
  .coc-card { position: relative; padding: 14px 14px 12px; }
  .coc-stage {
      position: relative; margin: 0 auto;
      border-radius: 14px; overflow: hidden;
      background: #0a0610;
      box-shadow: 0 6px 18px rgba(0,0,0,0.5),
                  inset 0 0 0 1px rgba(212,175,55,0.30);
  }
  .coc-canvas {
      position: absolute; top: 0; left: 0;
      display: block;
      /* Override the global `canvas { max-height: 300px }` rule. */
      max-height: none !important;
      max-width:  none !important;
  }
  .coc-status {
      position: absolute;
      left: 50%; top: 50%; transform: translate(-50%, -50%);
      font-size: 11px; font-style: italic;
      color: rgba(245, 235, 215, 0.7);
      padding: 6px 12px;
      background: rgba(0, 0, 0, 0.55);
      border-radius: 999px;
      pointer-events: none;
      transition: opacity 0.4s ease;
  }
  .coc-status[hidden] { opacity: 0; }
  .coc-label {
      position: absolute;
      left: 50%; bottom: 8px;
      transform: translateX(-50%);
      padding: 4px 12px;
      font-size: 11px; font-style: italic;
      color: rgba(245, 235, 215, 0.9);
      background: rgba(0, 0, 0, 0.65);
      border-radius: 999px;
      letter-spacing: 0.3px;
      max-width: 80%;
      white-space: nowrap; overflow: hidden;
      text-overflow: ellipsis;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.4s ease;
  }
  /* The name only appears once the user has explicitly revealed it
     (won the puzzle / hit 👁). Otherwise the label is empty so the
     mosaic stays a real "guess the card" — no spoiler flashing on draw
     or hover. */
  .coc-label.coc-revealed { opacity: 1; }
  /* Settings row chassis — matches the rest of the art cards. */
  .coc-fx-row {
      display: flex; flex-wrap: wrap; gap: 4px;
      align-items: center; margin-bottom: 6px;
  }
  .coc-fx-label {
      font-size: 10px; color: var(--muted);
      text-transform: uppercase; letter-spacing: 1px;
      min-width: 84px;
  }
  .coc-fx-btn {
      font-size: 10.5px;
      padding: 3px 8px;
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border: 1px solid var(--gold-3);
      border-radius: 999px;
      cursor: pointer;
      font-family: inherit;
      transition: background 0.12s ease, color 0.12s ease;
  }
  .coc-fx-btn:hover {
      background: rgba(212, 175, 55, 0.10);
      color: var(--gold-1);
  }
  .coc-fx-btn.active {
      background: var(--gold-2);
      color: #000;
      border-color: var(--gold-1);
      font-weight: 700;
  }
  .coc-fx-hint {
      margin: 4px 0 8px;
      font-size: 10.5px;
      color: var(--muted);
      line-height: 1.4;
      letter-spacing: 0.15px;
  }
  .coc-fx-hint em     { color: var(--gold-1); font-style: italic; }
  .coc-fx-hint strong { color: var(--gold-1); }
  /* "New Card" — sized + colored to read as the row's action,
     not just another option button. */
  .coc-fx-newcard {
      background: rgba(212, 175, 55, 0.18);
      color: var(--gold-1);
      font-size: 11.5px;
      padding: 5px 12px;
      font-weight: 700;
      letter-spacing: 0.4px;
  }
  .coc-fx-newcard:hover {
      background: rgba(212, 175, 55, 0.32);
  }
  /* Footer-level puzzle toggle — sits at the bottom-right of the
     card, level with the flavor text added by the framework. */
  .coc-puzzle-toggle {
      position: absolute;
      bottom: 8px; right: 10px;
      display: inline-flex; align-items: center; gap: 6px;
      padding: 4px 10px;
      background: rgba(8, 6, 18, 0.55);
      backdrop-filter: blur(3px);
      border: 1px solid var(--gold-3);
      border-radius: 999px;
      color: var(--text);
      font-family: inherit;
      font-size: 11px;
      letter-spacing: 0.3px;
      cursor: pointer;
      z-index: 5;
      transition: background 0.12s ease, color 0.12s ease;
  }
  .coc-puzzle-toggle:hover {
      background: rgba(212, 175, 55, 0.18);
      color: var(--gold-1);
  }
  .coc-puzzle-toggle.coc-puzzle-on {
      background: rgba(212, 175, 55, 0.32);
      color: var(--gold-1);
      border-color: var(--gold-1);
      font-weight: 700;
  }
  .coc-puzzle-toggle-icon { font-size: 13px; }
  /* Guess-the-card puzzle panel — sits in the lower-right, over
     the mosaic. Semi-transparent backdrop + blur so it reads as
     a HUD overlay rather than an interruption. */
  .coc-puzzle {
      position: absolute;
      right: 10px;
      bottom: 10px;
      max-width: 240px;
      padding: 10px 28px 8px 12px;     /* extra right pad for the × */
      background: rgba(8, 6, 18, 0.78);
      backdrop-filter: blur(6px);
      border: 1px solid var(--gold-3);
      border-radius: 10px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.55);
      z-index: 4;
  }
  .coc-puzzle[hidden] { display: none; }
  /* × close button — top-right of the puzzle panel. Dismissing
     turns puzzle mode OFF in settings so it doesn't reappear on
     refresh. (User can bring it back via the gear ⚙.) */
  .coc-puzzle-close {
      position: absolute;
      top: 2px; right: 4px;
      width: 22px; height: 22px;
      background: transparent;
      color: var(--muted);
      border: 0;
      font-size: 20px; line-height: 1;
      cursor: pointer;
      padding: 0;
      border-radius: 4px;
      transition: color 0.12s ease, background 0.12s ease;
  }
  .coc-puzzle-close:hover {
      color: var(--text);
      background: rgba(255, 255, 255, 0.08);
  }
  /* Reveal overlay: the actual subject card fades IN exactly OVER
     the mosaic at the same size, so it reads as "the mosaic
     resolves into the real card." JS positions the <img> to exactly
     match the mosaic canvas's bounding box. */
  .coc-reveal-img {
      position: absolute;
      object-fit: contain;
      opacity: 0;
      pointer-events: none;
      transition: opacity 1.1s ease;
      z-index: 3;
      filter: drop-shadow(0 12px 36px rgba(0, 0, 0, 0.7))
              drop-shadow(0 0 18px rgba(212, 175, 55, 0.45));
  }
  .coc-reveal-img.coc-reveal-show { opacity: 1; }
  .coc-reveal-img[hidden] { display: none; }
  /* Prev / next navigation arrows. Pinned to left + right inner
     edges of the stage, vertically centered. Big enough to hit,
     translucent enough not to dominate. */
  .coc-nav {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 34px; height: 60px;
      background: rgba(8, 6, 18, 0.62);
      backdrop-filter: blur(4px);
      border: 1px solid var(--gold-3);
      color: var(--gold-1);
      font-size: 26px; line-height: 1;
      cursor: pointer;
      padding: 0;
      display: flex; align-items: center; justify-content: center;
      z-index: 4;
      transition: background 0.12s ease, opacity 0.15s ease;
  }
  .coc-nav-prev { left: 6px;  border-radius: 6px 14px 14px 6px; }
  .coc-nav-next { right: 6px; border-radius: 14px 6px 6px 14px; }
  .coc-nav:hover { background: rgba(8, 6, 18, 0.85); }
  .coc-nav:disabled {
      opacity: 0.25; cursor: not-allowed;
      filter: grayscale(0.6);
  }
  .coc-puzzle-q {
      font-size: 11px;
      color: var(--gold-1);
      font-weight: 700;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
      text-align: center;
  }
  .coc-puzzle-opts {
      display: grid;
      grid-template-columns: 1fr;
      gap: 4px;
      margin-bottom: 6px;
  }
  .coc-puzzle-opt {
      font-size: 10.5px;
      padding: 6px 8px;
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border: 1px solid var(--gold-3);
      border-radius: 6px;
      cursor: pointer;
      text-align: left;
      font-family: inherit;
      letter-spacing: 0.2px;
      line-height: 1.25;
      transition: background 0.12s ease, transform 0.1s ease;
      white-space: normal;
      width: 100%;
      box-sizing: border-box;
  }
  .coc-puzzle-opt:hover {
      background: rgba(212, 175, 55, 0.12);
  }
  .coc-puzzle-opt.coc-correct {
      background: rgba(110, 200, 110, 0.30);
      border-color: #6ec86e;
      color: #d8ffd8;
  }
  .coc-puzzle-opt.coc-wrong {
      background: rgba(220, 90, 90, 0.30);
      border-color: #dc5a5a;
      color: #ffd8d8;
      animation: coc-shake 0.32s ease-in-out;
  }
  @keyframes coc-shake {
      0%,100% { transform: translateX(0); }
      25%     { transform: translateX(-4px); }
      75%     { transform: translateX(4px); }
  }
  .coc-puzzle-result {
      font-size: 11px;
      text-align: center;
      min-height: 14px;
      margin-bottom: 6px;
      letter-spacing: 0.2px;
  }
  .coc-puzzle-result.coc-result-win  { color: #b8f0b8; font-weight: 700; }
  .coc-puzzle-result.coc-result-lose { color: #f0b8b8; }
  .coc-puzzle-actions {
      display: flex;
      gap: 4px;
  }
  .coc-puzzle-actions button {
      flex: 1;
      font-size: 10px;
      padding: 4px 6px;
      background: rgba(212, 175, 55, 0.12);
      color: var(--gold-1);
      border: 1px solid var(--gold-3);
      border-radius: 6px;
      cursor: pointer;
      font-family: inherit;
      letter-spacing: 0.3px;
  }
  .coc-puzzle-actions button:hover { background: rgba(212, 175, 55, 0.22); }
</style>
"""


_COC_JS = r"""
(function () {
  const DEFAULTS = {
    subject: 'top', resolution: 24, tilekind: 'card', reveal: 'build',
    puzzle: 'off', tilepool: 80,
  };
  const INT_KEYS = new Set(['resolution', 'tilepool']);
  // Keys that we DON'T persist across page loads — they're transient
  // session state. Puzzle mode resets to OFF on every reload so the
  // mosaic comes up "clean" — the user has to explicitly start the
  // game each session.
  const TRANSIENT_KEYS = ['puzzle'];
  function loadCfg() {
    try {
      const s = JSON.parse(localStorage.getItem('cc-coc-cfg') || '{}');
      const merged = Object.assign({}, DEFAULTS, s);
      // Force transient keys back to their defaults regardless of
      // what was stored.
      for (const k of TRANSIENT_KEYS) merged[k] = DEFAULTS[k];
      return merged;
    } catch (e) { return Object.assign({}, DEFAULTS); }
  }
  function saveCfg(cfg) {
    try {
      const toSave = Object.assign({}, cfg);
      for (const k of TRANSIENT_KEYS) delete toSave[k];
      localStorage.setItem('cc-coc-cfg', JSON.stringify(toSave));
    } catch (e) {}
  }

  // CORS-clean image loader via /scryfall-img proxy. Returns a
  // promise resolving to an HTMLImageElement we can drawImage AND
  // getImageData from (canvas stays untainted).
  const _imgCache = new Map();
  function loadImage(url) {
    if (!url) return Promise.reject(new Error('no url'));
    if (_imgCache.has(url)) return _imgCache.get(url);
    const proxied = url.startsWith('https://cards.scryfall.io/')
      ? '/scryfall-img?url=' + encodeURIComponent(url)
      : url;
    const p = new Promise((resolve, reject) => {
      const im = new Image();
      im.crossOrigin = 'anonymous';
      im.onload = () => resolve(im);
      im.onerror = () => reject(new Error('load failed: ' + url));
      im.src = proxied;
    });
    _imgCache.set(url, p);
    return p;
  }

  // Compute average RGB of an image by drawing it into a small
  // scratch canvas + reading pixels. Tiles use the WHOLE image
  // (because we want the perceived color of the thumbnail itself),
  // not just a region.
  const _avgCache = new WeakMap();
  function averageColor(img) {
    if (_avgCache.has(img)) return _avgCache.get(img);
    const c = document.createElement('canvas');
    const S = 12;        // downsample to 12x12 for speed
    c.width = c.height = S;
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(img, 0, 0, S, S);
    let r = 0, g = 0, b = 0, n = 0;
    try {
      const d = ctx.getImageData(0, 0, S, S).data;
      for (let i = 0; i < d.length; i += 4) {
        // Skip alpha=0 (transparent corners), and almost-pure-black
        // (card borders) so the avg isn't dragged toward 0.
        if (d[i + 3] < 8) continue;
        if (d[i] + d[i+1] + d[i+2] < 24) continue;
        r += d[i]; g += d[i + 1]; b += d[i + 2]; n++;
      }
    } catch (e) {
      // Canvas was tainted (proxy hiccup); fall back to mid-grey.
      _avgCache.set(img, [128, 128, 128]);
      return [128, 128, 128];
    }
    const out = n > 0 ? [Math.round(r/n), Math.round(g/n), Math.round(b/n)]
                       : [128, 128, 128];
    _avgCache.set(img, out);
    return out;
  }

  function colorDist(a, b) {
    const dr = a[0] - b[0], dg = a[1] - b[1], db = a[2] - b[2];
    return dr * dr + dg * dg + db * db;
  }

  function initStage(stage) {
    if (stage.dataset.cocInited === '1') return;
    stage.dataset.cocInited = '1';

    let subjects;
    let ALL_TILES;
    try { subjects = JSON.parse(stage.dataset.cocSubjects || '[]'); }
    catch (e) { subjects = []; }
    try { ALL_TILES = JSON.parse(stage.dataset.cocTiles   || '[]'); }
    catch (e) { ALL_TILES = []; }
    if (!subjects.length || ALL_TILES.length < 8) return;
    // tiles is re-derived from ALL_TILES each build so the Tile-pool
    // slider takes effect without a page reload.
    let tiles = ALL_TILES.slice(0, 80);

    const cardRoot   = stage.closest('.coc-card');
    const canvas     = stage.querySelector('.coc-canvas');
    const status     = stage.querySelector('.coc-status');
    const label      = stage.querySelector('.coc-current');
    const gear       = cardRoot && cardRoot.querySelector('.coc-gear-trigger');
    const panel      = cardRoot && cardRoot.querySelector('.coc-pop');
    const puzzleBox   = stage.querySelector('.coc-puzzle');
    const puzzleOpts  = stage.querySelector('.coc-puzzle-opts');
    const puzzleRes   = stage.querySelector('.coc-puzzle-result');
    const puzzleSwap  = stage.querySelector('.coc-puzzle-swap');
    const puzzleRev   = stage.querySelector('.coc-puzzle-reveal');
    const puzzleClose = stage.querySelector('.coc-puzzle-close');
    const revealImg   = stage.querySelector('.coc-reveal-img');
    const navPrev     = stage.querySelector('.coc-nav-prev');
    const navNext     = stage.querySelector('.coc-nav-next');
    const puzzleToggle = cardRoot
                         && cardRoot.querySelector('.coc-puzzle-toggle');
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });

    let cfg = loadCfg();
    function refreshActive() {
      if (!panel) return;
      panel.querySelectorAll('.coc-fx-btn').forEach(b => {
        const k = b.dataset.fx;
        if (!k) return;
        b.classList.toggle('active', String(cfg[k]) === b.dataset.v);
      });
      panel.querySelectorAll('.coc-fx-slider[data-fx]').forEach(sl => {
        sl.value = String(cfg[sl.dataset.fx]);
      });
      panel.querySelectorAll('.coc-fx-out[data-out]').forEach(o => {
        o.textContent = String(cfg[o.dataset.out]);
      });
    }

    // Stage size — fixed pixel square. The CANVAS sizing is owned
    // entirely by build() (which sizes it to the subject aspect,
    // centered). resize() only touches the stage dimensions. If
    // the stage size changes after a build, we trigger a rebuild
    // with keepSubject:true so the canvas paints fresh at the new
    // dimensions — previously resize() set canvas.width every tick
    // which CLEARED the canvas mid-build-up, leaving the user with
    // a sparsely-painted mosaic on first load.
    let lastStageSide = 0;
    function resize() {
      const card = stage.closest('.coc-card');
      if (!card) return;
      const cs = getComputedStyle(card);
      const cw = card.clientWidth
                 - parseFloat(cs.paddingLeft || '0')
                 - parseFloat(cs.paddingRight || '0');
      if (cw < 40) return;
      const side = Math.round(cw);
      stage.style.width  = side + 'px';
      stage.style.height = side + 'px';
      if (window.__ccMasonryPack) {
        try { window.__ccMasonryPack(); } catch (_) {}
      }
      // If the stage GREW significantly between resize calls AND
      // we've already built once, trigger a fresh build at the new
      // size. The size-change threshold (20px) avoids ping-pong on
      // tiny layout jitters.
      if (lastStageSide > 0
          && Math.abs(side - lastStageSide) > 20
          && currentSubject) {
        lastStageSide = side;
        build({ keepSubject: true });
      } else if (lastStageSide === 0) {
        lastStageSide = side;
      }
    }
    resize();
    setTimeout(resize, 200);
    setTimeout(resize, 800);
    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(resize);
      ro.observe(stage.closest('.coc-card'));
    }

    // Pick subject based on cfg.subject:
    //   "top"    → random pick from the user's TOP 15 most valuable
    //               cards (since just returning subjects[0] every
    //               time made re-clicks feel broken — "top value"
    //               now means "pick a top card", not "always #1").
    //   "random" → random pick from the FULL collection (subjects
    //               is now the entire pool, not a top-N slice).
    // We avoid repeating the previous subject so swap actually
    // changes things even with a small pool.
    let lastSubjectName = null;
    const TOP_VALUE_N = 15;
    function pickSubject(forceDifferent) {
      const sourcePool =
        (cfg.subject === 'top')
          ? subjects.slice(0, Math.min(TOP_VALUE_N, subjects.length))
          : subjects;
      if (!sourcePool.length) return subjects[0];
      // Avoid recently-seen subjects (the last few from history) so
      // pressing "next" rapidly doesn't surface the same handful of
      // cards. We bias against the LAST 5; further-back is fair game.
      const recent = new Set(
        history.slice(Math.max(0, history.length - 5))
               .map(s => s.name));
      for (let i = 0; i < 20; i++) {
        const pick = sourcePool[Math.floor(Math.random() * sourcePool.length)];
        if (recent.has(pick.name)) continue;
        return pick;
      }
      // Fall through after retries — pool smaller than recent
      // window, or just unlucky. Return anything that isn't the
      // immediately-previous one if possible.
      for (let i = 0; i < 8; i++) {
        const pick = sourcePool[Math.floor(Math.random() * sourcePool.length)];
        if (pick.name !== lastSubjectName) return pick;
      }
      return sourcePool[Math.floor(Math.random() * sourcePool.length)];
    }

    let buildToken = 0;
    let currentSubject = null;
    // History stack of subjects the user has seen. Prev/next walk
    // this so the user can always step one back. `histIdx` is the
    // index of the CURRENT subject within history (== length-1
    // when on the most recent, < length-1 when paged back).
    const history = [];
    let histIdx = -1;
    function refreshNavButtons() {
      if (navPrev) navPrev.disabled = (histIdx <= 0);
      // navNext is always enabled — it picks a new subject.
    }
    // Build the mosaic. Options:
    //   subject       — explicit subject to use (history walk).
    //   keepSubject   — true → reuse currentSubject (resolution /
    //                   tilekind / reveal toggles use this so the
    //                   visible card doesn't change when the user
    //                   only changes a render setting).
    //   forceDifferent — true → pickSubject() must NOT return the
    //                   previous one (used by ↻ swap / next).
    async function build(opts) {
      opts = opts || {};
      const myToken = ++buildToken;
      // Re-derive the tile pool from the current slider value so a
      // settings change takes effect on the next build.
      const tilePool = Math.max(8, Math.min(ALL_TILES.length,
                                  parseInt(cfg.tilepool, 10) || 80));
      tiles = ALL_TILES.slice(0, tilePool);
      status.hidden = false;
      status.textContent = 'Loading subject…';
      let subject;
      if (opts.subject) {
        subject = opts.subject;
      } else if (opts.keepSubject && currentSubject) {
        subject = currentSubject;
      } else {
        subject = pickSubject(opts.forceDifferent);
        // New (forward) subject — append to history + advance cursor.
        history.push(subject);
        histIdx = history.length - 1;
      }
      currentSubject = subject;
      lastSubjectName = subject.name;
      refreshNavButtons();
      // Hide the reveal image on every new build so the previous
      // subject's card doesn't linger on top of the new mosaic.
      if (revealImg) {
        revealImg.classList.remove('coc-reveal-show');
        revealImg.hidden = true;
      }
      // Sync the puzzle overlay + footer toggle visual state with
      // cfg.puzzle. (applyPuzzleMode is idempotent + safe to call
      // for both 'on' and 'off' values.)
      applyPuzzleMode();
      // 1) Load the subject image.
      let subjImg;
      try { subjImg = await loadImage(subject.image); }
      catch (e) { status.textContent = 'subject failed'; return; }
      if (myToken !== buildToken) return;
      // 2) Load tile images IN PARALLEL with a max-concurrency limit.
      status.textContent = `Loading ${tiles.length} tiles…`;
      const tileImgs = [];
      const tileAvgs = [];
      // Concurrent loader pool (8 at a time keeps the network busy
      // without thrashing the decoder).
      let idx = 0;
      async function worker() {
        while (idx < tiles.length && myToken === buildToken) {
          const i = idx++;
          try {
            const im = await loadImage(tiles[i].image);
            tileImgs[i] = im;
            tileAvgs[i] = averageColor(im);
          } catch (_) {
            tileImgs[i] = null;
            tileAvgs[i] = null;
          }
        }
      }
      const workers = [];
      for (let w = 0; w < 8; w++) workers.push(worker());
      await Promise.all(workers);
      if (myToken !== buildToken) return;
      // 3) Compute the cell color grid + tile sizes.
      // The subject is card-shaped (aspect ≈ 0.72 width/height), so
      // we fit a card-shaped mosaic INSIDE the square stage rather
      // than squishing the subject into a square. Tile shape ("card"
      // vs "square") only changes how individual tiles render — the
      // OVERALL mosaic dimensions track the subject aspect either way.
      const cols = Math.max(8, Math.min(40,
                                          parseInt(cfg.resolution, 10) || 24));
      const aspect = subjImg.naturalHeight / subjImg.naturalWidth;
      const stageW = stage.clientWidth;
      const stageH = stage.clientHeight;
      // Fit the mosaic to the stage with subject aspect preserved.
      let mosaicW = stageW * 0.96;
      let mosaicH = mosaicW * aspect;
      if (mosaicH > stageH * 0.96) {
        mosaicH = stageH * 0.96;
        mosaicW = mosaicH / aspect;
      }
      const tileW = Math.floor(mosaicW / cols);
      const tileH = (cfg.tilekind === 'card')
                    ? Math.round(tileW * 1.40)
                    : tileW;
      const rows = Math.max(1, Math.round(mosaicH / tileH));
      const totalW = tileW * cols;
      const totalH = tileH * rows;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width  = totalW * dpr;
      canvas.height = totalH * dpr;
      // Center the canvas within the stage.
      canvas.style.width  = totalW + 'px';
      canvas.style.height = totalH + 'px';
      canvas.style.left = Math.round((stageW - totalW) / 2) + 'px';
      canvas.style.top  = Math.round((stageH - totalH) / 2) + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      // Sample the subject — each cell gets the average color of its
      // corresponding region of the subject image.
      const sc = document.createElement('canvas');
      sc.width = cols; sc.height = rows;
      const sctx = sc.getContext('2d', { willReadFrequently: true });
      sctx.drawImage(subjImg, 0, 0, cols, rows);
      let targets;
      try {
        targets = sctx.getImageData(0, 0, cols, rows).data;
      } catch (e) {
        status.textContent = 'subject canvas tainted'; return;
      }
      // 4) Build the cell→tile assignment. Greedy: for each cell,
      // pick the tile with the closest avg color.
      ctx.fillStyle = '#0a0610';
      ctx.fillRect(0, 0, totalW, totalH);
      status.hidden = true;
      const validTileIdxs = [];
      for (let i = 0; i < tiles.length; i++) {
        if (tileImgs[i] && tileAvgs[i]) validTileIdxs.push(i);
      }
      if (!validTileIdxs.length) {
        status.hidden = false;
        status.textContent = 'no usable tile images';
        return;
      }
      // 5) Draw — instant or build-up.
      const placements = [];
      for (let cy = 0; cy < rows; cy++) {
        for (let cx = 0; cx < cols; cx++) {
          const o = (cy * cols + cx) * 4;
          const tgt = [targets[o], targets[o + 1], targets[o + 2]];
          let best = validTileIdxs[0];
          let bestD = colorDist(tileAvgs[best], tgt);
          for (const ti of validTileIdxs) {
            const d = colorDist(tileAvgs[ti], tgt);
            if (d < bestD) { best = ti; bestD = d; }
          }
          placements.push({
            x: cx * tileW, y: cy * tileH,
            tileIdx: best,
          });
        }
      }
      if (cfg.reveal === 'instant') {
        for (const p of placements) drawTile(p, tileImgs[p.tileIdx]);
      } else {
        // build-up: shuffle placement order, then draw N per frame
        for (let i = placements.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [placements[i], placements[j]] = [placements[j], placements[i]];
        }
        const PER_FRAME = Math.max(4, Math.floor(placements.length / 60));
        let cursor = 0;
        function frame() {
          if (myToken !== buildToken) return;
          const end = Math.min(cursor + PER_FRAME, placements.length);
          for (let i = cursor; i < end; i++) {
            const p = placements[i];
            drawTile(p, tileImgs[p.tileIdx]);
          }
          cursor = end;
          if (cursor < placements.length) requestAnimationFrame(frame);
        }
        requestAnimationFrame(frame);
      }
      function drawTile(p, img) {
        if (!img) return;
        if (cfg.tilekind === 'card') {
          // Draw with rounded corners to mimic a tiny card.
          ctx.save();
          const r = Math.max(1, tileW * 0.08);
          const x = p.x, y = p.y;
          roundedRectPath(ctx, x, y, tileW, tileH, r);
          ctx.clip();
          ctx.drawImage(img, x, y, tileW, tileH);
          ctx.restore();
        } else {
          ctx.drawImage(img, p.x, p.y, tileW, tileH);
        }
      }
      function roundedRectPath(c, x, y, w, h, r) {
        c.beginPath();
        c.moveTo(x + r, y);
        c.lineTo(x + w - r, y);
        c.quadraticCurveTo(x + w, y, x + w, y + r);
        c.lineTo(x + w, y + h - r);
        c.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        c.lineTo(x + r, y + h);
        c.quadraticCurveTo(x, y + h, x, y + h - r);
        c.lineTo(x, y + r);
        c.quadraticCurveTo(x, y, x + r, y);
        c.closePath();
      }
    }

    // ---- Puzzle: multiple-choice "guess the card" ----
    // When cfg.puzzle === 'on' the label is hidden ("??? ???") and
    // the panel shows 4 buttons — 1 correct, 3 distractors picked
    // from other subject candidates. Clicking the correct one wins
    // and reveals the name; wrong shakes red and lets the user try
    // again. Swap rebuilds with a different subject (forces a new
    // one); Reveal just shows the answer.
    function shuffle(arr) {
      const a = arr.slice();
      for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
      }
      return a;
    }
    function setupPuzzle(subject) {
      if (!puzzleBox) return;
      puzzleBox.hidden = false;
      puzzleRes.textContent = '';
      puzzleRes.className = 'coc-puzzle-result';
      // Build distractor pool: subject candidates whose name isn't
      // the answer. Pick 3 at random.
      const others = subjects.filter(s => s.name !== subject.name);
      const distractors = shuffle(others).slice(0, 3);
      const choices = shuffle([subject, ...distractors]);
      puzzleOpts.innerHTML = '';
      choices.forEach(c => {
        const btn = document.createElement('button');
        btn.className = 'coc-puzzle-opt';
        btn.type = 'button';
        btn.dataset.name = c.name;
        btn.textContent = c.name;
        puzzleOpts.appendChild(btn);
      });
    }
    function revealAnswer(text) {
      if (!currentSubject) return;
      label.textContent = currentSubject.name;
      label.classList.add('coc-revealed');
      puzzleRes.textContent = text || `It was ${currentSubject.name}.`;
      puzzleRes.classList.add('coc-result-lose');
      // Mark the correct button so the user learns which it was.
      puzzleOpts.querySelectorAll('.coc-puzzle-opt').forEach(b => {
        if (b.dataset.name === currentSubject.name) {
          b.classList.add('coc-correct');
        }
      });
      showRevealImg();
    }
    // Fade the actual subject card image in over the mosaic. Called
    // on a correct guess AND on 👁 reveal. Resets cleanly when the
    // puzzle is reset / next subject is loaded.
    // Switch the puzzle overlay on/off WITHOUT rebuilding the mosaic.
    // Use the currently-displayed subject so the user can finally
    // see "now I want to guess this exact one!" workflow work.
    function applyPuzzleMode() {
      if (!currentSubject) return;
      // Never auto-show the subject name — the mosaic is a guessing game.
      // The name is only set + made visible by an explicit reveal (win /
      // 👁). On every (re)build we clear it so the answer can't leak.
      label.classList.remove('coc-revealed');
      label.textContent = '';
      if (cfg.puzzle === 'on') {
        setupPuzzle(currentSubject);
      } else {
        if (puzzleBox) puzzleBox.hidden = true;
        hideRevealImg();
      }
      if (puzzleToggle) {
        puzzleToggle.classList.toggle('coc-puzzle-on',
                                       cfg.puzzle === 'on');
        const lbl = puzzleToggle.querySelector('.coc-puzzle-toggle-label');
        if (lbl) lbl.textContent =
          (cfg.puzzle === 'on') ? 'End puzzle' : 'Guess the card';
      }
    }
    function showRevealImg() {
      if (!revealImg || !currentSubject) return;
      const src = currentSubject.image.startsWith('https://cards.scryfall.io/')
        ? '/scryfall-img?url=' + encodeURIComponent(currentSubject.image)
        : currentSubject.image;
      revealImg.src = src;
      revealImg.alt = currentSubject.name;
      // Reveal fills the ENTIRE stage so it visibly extends past the
      // mosaic canvas (which is card-aspect and centered with margin).
      // User wants the revealed card to cover all the dark space around
      // the painted mosaic, not just the mosaic itself.
      revealImg.style.left   = '0px';
      revealImg.style.top    = '0px';
      revealImg.style.width  = '100%';
      revealImg.style.height = '100%';
      revealImg.hidden = false;
      void revealImg.offsetWidth;   // reflow → transition fires
      revealImg.classList.add('coc-reveal-show');
    }
    function hideRevealImg() {
      if (!revealImg) return;
      revealImg.classList.remove('coc-reveal-show');
      // Defer the hidden flip until the fade-out finishes so the
      // user sees a smooth dismiss.
      setTimeout(() => { revealImg.hidden = true; }, 700);
    }
    if (puzzleOpts) {
      puzzleOpts.addEventListener('click', e => {
        const btn = e.target.closest('.coc-puzzle-opt');
        if (!btn || !currentSubject) return;
        if (btn.classList.contains('coc-correct') ||
            btn.classList.contains('coc-wrong')) return;
        const correct = btn.dataset.name === currentSubject.name;
        if (correct) {
          btn.classList.add('coc-correct');
          puzzleRes.textContent = `🎉 Correct — ${currentSubject.name}!`;
          puzzleRes.classList.add('coc-result-win');
          label.textContent = currentSubject.name;
          label.classList.add('coc-revealed');
          showRevealImg();
        } else {
          btn.classList.add('coc-wrong');
          btn.disabled = true;
        }
      });
    }
    if (puzzleClose) {
      puzzleClose.addEventListener('click', e => {
        e.stopPropagation();
        // Turn puzzle mode OFF + persist, so a refresh doesn't bring
        // the panel back. User can re-enable from the gear.
        cfg.puzzle = 'off';
        saveCfg(cfg);
        refreshActive();
        if (puzzleBox) puzzleBox.hidden = true;
        // Don't spoil on close — leave the label as-is (it already shows
        // the name if they revealed/won, blank otherwise).
        hideRevealImg();
      });
    }
    if (puzzleSwap) {
      puzzleSwap.addEventListener('click', e => {
        e.stopPropagation();
        build({ forceDifferent: true });
      });
    }
    if (puzzleRev) {
      puzzleRev.addEventListener('click', e => {
        e.stopPropagation();
        revealAnswer();
      });
    }

    // Wire settings popover (same as other art cards).
    if (gear && panel) {
      gear.addEventListener('click', e => {
        e.stopPropagation();
        panel.hidden = !panel.hidden;
      });
      document.addEventListener('click', e => {
        if (panel.hidden) return;
        if (panel.contains(e.target)) return;
        if (e.target === gear) return;
        panel.hidden = true;
      });
      // Sliders (tile pool, etc.) — rebuild with the same subject on
      // each input event so the user sees the change live.
      panel.addEventListener('input', e => {
        const sl = e.target.closest('.coc-fx-slider[data-fx]');
        if (!sl) return;
        const k = sl.dataset.fx;
        cfg[k] = INT_KEYS.has(k) ? parseInt(sl.value, 10) : sl.value;
        saveCfg(cfg);
        refreshActive();
        build({ keepSubject: true });
      });
      panel.addEventListener('click', e => {
        e.stopPropagation();
        // "↻ remix" — explicit user request to swap the subject.
        if (e.target.closest('[data-coc-regen]')) {
          build({ forceDifferent: true });
          return;
        }
        const b = e.target.closest('.coc-fx-btn');
        if (!b || !b.dataset.fx) return;
        const k = b.dataset.fx;
        cfg[k] = INT_KEYS.has(k) ? parseInt(b.dataset.v, 10)
                                  : b.dataset.v;
        saveCfg(cfg); refreshActive();
        // Decide whether the change requires a SUBJECT switch or
        // just a render refresh with the SAME subject:
        //   - puzzle   → only toggles the overlay; no rebuild.
        //   - subject  → user is changing pool ("top" vs "random");
        //                next subject pick will reflect that, but we
        //                keep the current card on screen until they
        //                ask for a new one (via next or ↻ remix).
        //   - everything else (resolution, tilekind, reveal) → just
        //                re-render the same subject with new params.
        //                User asked: high/med/low + card/square +
        //                build/instant should NEVER change the card.
        if (k === 'puzzle') {
          applyPuzzleMode();
        } else if (k === 'subject') {
          // No-op — change takes effect on next/swap/remix.
        } else {
          build({ keepSubject: true });
        }
      });
    }
    // ---- Footer puzzle toggle (sits next to the flavor text) ----
    if (puzzleToggle) {
      puzzleToggle.addEventListener('click', e => {
        e.stopPropagation();
        cfg.puzzle = (cfg.puzzle === 'on') ? 'off' : 'on';
        saveCfg(cfg);
        refreshActive();
        applyPuzzleMode();
      });
    }
    // ---- Prev / next nav arrows ----
    if (navPrev) {
      navPrev.addEventListener('click', e => {
        e.stopPropagation();
        if (histIdx <= 0) return;
        histIdx--;
        build({ subject: history[histIdx] });
      });
    }
    if (navNext) {
      navNext.addEventListener('click', e => {
        e.stopPropagation();
        // If the user paged BACK through history, "next" should
        // step FORWARD through history first; only when they're
        // on the most recent does it pick a brand-new subject.
        if (histIdx < history.length - 1) {
          histIdx++;
          build({ subject: history[histIdx] });
        } else {
          build({ forceDifferent: true });
        }
      });
    }

    refreshActive();
    // Defer the first build until the stage is actually visible + sized.
    // When the card sits on a tab/section that's display:none at load,
    // stage.clientWidth/Height are 0, so the mosaic drew into a 0×0 canvas
    // and looked blank until the user clicked an arrow (which rebuilt once
    // the card was on-screen). Build as soon as it has real dimensions.
    function tryFirstBuild() {
      if (stage.clientWidth > 0 && stage.clientHeight > 0) { build(); return true; }
      return false;
    }
    if (!tryFirstBuild()) {
      if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver(entries => {
          for (const en of entries) {
            if (en.isIntersecting && tryFirstBuild()) { io.disconnect(); break; }
          }
        }, { threshold: 0.01 });
        io.observe(stage);
      } else {
        let tries = 0;
        const t = setInterval(() => {
          if (tryFirstBuild() || ++tries > 40) clearInterval(t);
        }, 150);
      }
    }
  }

  function initAll() {
    document.querySelectorAll('.coc-stage').forEach(initStage);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
  document.addEventListener('cc-rerender', initAll);
})();
"""
