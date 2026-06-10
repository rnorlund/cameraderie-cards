"""cc_cortex.py — Cortex dashboard card.

A real anatomical brain (ICBM-152 cortical surface) rendered in 3D, with
the user's selected cards' art projected onto / drifting across the
cortex. Three visual "looks" (chosen via gear): flowing projection,
drifting decals, synaptic pulse.

Card selection: auto-seeded with the top-N most valuable cards; the user
can swap individual cards in/out via the gear (the seed always fills it
so it works out of the box).

The brain mesh is parsed in-browser from the bundled .mz3 (gunzip via
DecompressionStream); rendering is Three.js (CDN ES module). Niivue is
not used — it's a scalar/medical viewer, not an image-texture projector.

Registered in cc_cards.py at module-load time.
"""
from __future__ import annotations

import html as _html
import json as _json
import re as _re

__all__ = ["render_cortex_card", "select_cards", "CORTEX_CATALOG_ENTRY"]


CORTEX_CATALOG_ENTRY = {
    "key": "cortex",
    "label": "🧠 Cortex",
    "desc": "Your cards, projected onto a living brain. Pick the cards to "
            "feature and watch their art drift across a real anatomical "
            "cortex — a museum specimen made of your collection.",
    "type_line": "Visualization — Cortex",
    "flavor": "Every collection has a mind of its own.",
    "default_w": 3, "default_h": 2, "min_w": 2, "min_h": 2,
}

# Bundled brain mesh. Served via the /assets/ route (which allows
# sub-directories); the /asset/ route is filename-only and would 404.
CORTEX_MESH_URL = "/assets/cortex/BrainMesh_ICBM152.lh.mz3"

# default number of cards to feature
DEFAULT_N = 12


def _color_bucket(colors) -> str:
    s = set((c or "").upper() for c in (colors or []))
    if not s:
        return "C"
    if len(s) >= 2:
        return "M"
    return next(iter(s))


_MANA_HUE = {
    "W": "#f5e3a0", "U": "#3f78c4", "B": "#7a5a86",
    "R": "#c0382a", "G": "#388f44", "M": "#d4af37", "C": "#b9c2b9",
}


def _excerpt(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def select_cards(all_items, n: int = DEFAULT_N,
                 picks: list[str] | None = None) -> list[dict]:
    """Choose the cards to feature on the brain.

    Deduped by name. If `picks` (a list of card names) is given, those are
    used in order (still backfilled with art/meta); otherwise the top-`n`
    by total value (unit × qty) seed it. Each returned card carries the
    art-crop URL (for the surface) + full image (for the dossier) + meta.
    """
    by_name: dict[str, dict] = {}
    for r in all_items or []:
        if r.get("category") == "Sealed":
            continue
        name = (r.get("card_name") or r.get("matched")
                or r.get("card") or r.get("name") or "").strip()
        if not name:
            continue
        unit = float(r.get("unit") or 0)
        qty = int(r.get("qty") or 1)
        total = unit * qty
        prev = by_name.get(name)
        if prev is not None and total <= prev["_total"]:
            continue
        legal = r.get("legalities") or []
        if isinstance(legal, dict):
            legal = [k for k, v in legal.items() if v == "legal"]
        by_name[name] = {
            "name": name,
            "_total": total,
            "unit": round(unit, 2),
            "qty": qty,
            "colors": r.get("color_identity") or r.get("colors") or [],
            "rarity": (r.get("rarity") or "").lower(),
            "image": (r.get("image_normal") or r.get("image")
                      or r.get("image_small") or ""),
            "art": (r.get("art_crop") or ""),
            "set": (r.get("matched_set") or r.get("set") or ""),
            "released_at": r.get("released_at") or "",
            "type_line": (r.get("type_line") or "").strip(),
            "mana_cost": (r.get("mana_cost") or "").strip(),
            "cmc": r.get("cmc"),
            "oracle_text": (r.get("oracle_text") or "").strip(),
            "flavor_text": (r.get("flavor_text") or "").strip(),
            "artist": (r.get("artist") or "").strip(),
            "reserved": bool(r.get("reserved")),
            "legalities": [str(x).lower() for x in legal if x][:10],
            "scryfall_uri": r.get("scryfall_uri") or "",
            "oracle_id": (r.get("oracle_id") or "").strip(),
        }

    cards = list(by_name.values())
    _backfill_art(cards)

    if picks:
        chosen = [by_name[p] for p in picks if p in by_name]
        if not chosen:
            chosen = sorted(cards, key=lambda c: -c["_total"])[:n]
    else:
        chosen = sorted(cards, key=lambda c: -c["_total"])[:max(1, n)]

    # per-card reprint risk from the trained model (if loaded)
    try:
        import cc_reprint_model
    except Exception:
        cc_reprint_model = None

    out = []
    for c in chosen:
        cb = _color_bucket(c.get("colors"))
        year = c.get("released_at") or ""
        year = year[:4] if isinstance(year, str) and year[:4].isdigit() else ""
        pred = None
        if cc_reprint_model is not None:
            try:
                pred = cc_reprint_model.lookup(c.get("oracle_id"), c["name"])
            except Exception:
                pred = None
        cmc = c.get("cmc")
        try:
            cmc = int(cmc) if cmc is not None and float(cmc) == int(float(cmc)) else cmc
        except (TypeError, ValueError):
            pass
        out.append({
            "name": c["name"],
            "art": c.get("art") or c.get("image") or "",
            "image": c.get("image") or c.get("art") or "",
            "set": c["set"],
            "year": year,
            "unit": c["unit"],
            "qty": c["qty"],
            "type_line": c["type_line"],
            "mana_cost": c.get("mana_cost") or "",
            "cmc": cmc,
            "artist": c["artist"],
            "rarity": c["rarity"],
            "reserved": bool(c.get("reserved")),
            "oracle_text": c.get("oracle_text") or "",
            "oracle_excerpt": _excerpt(c.get("oracle_text") or "", 150),
            "flavor_text": c.get("flavor_text") or "",
            "legalities": c.get("legalities") or [],
            "reprint_p12": (pred["p12"] if pred else None),
            "reprint_rank": (pred["rank"] if pred else None),
            "scryfall_uri": c["scryfall_uri"],
            "color": cb,
            "accent": _MANA_HUE.get(cb, "#d4af37"),
        })
    return out


def _backfill_art(cards: list[dict]) -> None:
    """Fill art_crop / image / colors / meta from the bulk Scryfall DB for
    cards whose priced record lacked them (and to get the art-crop URL,
    which the priced record never stores)."""
    try:
        from cc_pricing import _bulk_get_conn
        conn = _bulk_get_conn()
    except Exception:
        conn = None
    if conn is None:
        return
    for c in cards:
        # Only skip the DB lookup when the fields the dossier needs are all
        # present. (flavor_text is legitimately often empty, so it doesn't
        # force a lookup.)
        if c.get("art") and c.get("image") and c.get("colors") \
                and c.get("oracle_text") and c.get("type_line") \
                and c.get("mana_cost") is not None and c.get("legalities"):
            continue
        try:
            rows = list(conn.execute(
                "SELECT data_json FROM cards WHERE name_lower = ?",
                (c["name"].lower(),)))
        except Exception:
            continue
        if not rows:
            continue
        best = None
        for (dj,) in rows:
            try:
                d = _json.loads(dj)
            except Exception:
                continue
            best = d
            # prefer a printing that actually has an art_crop
            uris = d.get("image_uris") or {}
            if uris.get("art_crop"):
                break
        if not best:
            continue
        face = (best.get("card_faces") or [{}])[0]
        uris = best.get("image_uris") or face.get("image_uris") or {}
        if not c.get("art"):
            c["art"] = uris.get("art_crop") or ""
        if not c.get("image"):
            c["image"] = (uris.get("normal") or uris.get("large")
                          or uris.get("small") or "")
        if not c.get("colors"):
            c["colors"] = (best.get("color_identity") or best.get("colors")
                           or face.get("colors") or [])
        if not c.get("oracle_text"):
            c["oracle_text"] = (best.get("oracle_text")
                                or face.get("oracle_text") or "")
        if not c.get("type_line"):
            c["type_line"] = (best.get("type_line")
                              or face.get("type_line") or "")
        if not c.get("mana_cost"):
            c["mana_cost"] = (best.get("mana_cost")
                              or face.get("mana_cost") or "")
        if c.get("cmc") is None:
            c["cmc"] = best.get("cmc")
        if not c.get("flavor_text"):
            c["flavor_text"] = (best.get("flavor_text")
                                or face.get("flavor_text") or "")
        if not c.get("legalities"):
            leg = best.get("legalities") or {}
            c["legalities"] = [k for k, v in leg.items()
                               if v == "legal"][:10]
        if "reserved" not in c or c.get("reserved") is None:
            c["reserved"] = bool(best.get("reserved"))
        if not c.get("artist"):
            c["artist"] = best.get("artist") or ""
        if not c.get("scryfall_uri"):
            c["scryfall_uri"] = best.get("scryfall_uri") or ""
        if not c.get("released_at"):
            c["released_at"] = best.get("released_at") or ""


# Pool size: the client loads this many cards once; the gear's "count"
# slider then shows the first N live (no reload), and order/group modes
# reorder client-side. 24 covers the slider's max.
POOL_N = 24

# Default gear settings; merged with saved panes.cortex prefs.
DEFAULT_SETTINGS = {
    "count": DEFAULT_N,    # cards shown in the ribbon (3..POOL_N)
    "order": "value",      # value | color | recent | random
    "pattern": "ribbon",   # ribbon | wrap | spiral | vertical
    "speed": 5.0,          # flow speed (0..10)
    "bright": 1.15,        # art brightness (0.4..2.0)
    "pulseRate": 0.0,      # pulse cycles/sec (0 = off)
    "pulseAmt": 0.0,       # pulse depth (0..1)
    "band": 0.66,          # ribbon width (0.1..1.0)
    "rim": 0.35,           # gold rim glow (0..1.2)
    "legible": 0.55,       # card legibility: 0 = shaded into cortex, 1 = flat & bright
    "spin": "on",          # on | off
    # screen-corner stage lights — user-choosable hues; black = off
    "lightTL": "#000000", "lightTR": "#000000",
    "lightBL": "#000000", "lightBR": "#000000",
}
_SETTING_KEYS = set(DEFAULT_SETTINGS)


def render_cortex_card(ctx: dict, variant: str | None = None,
                       n: int = DEFAULT_N,
                       picks: list[str] | None = None) -> str:
    prefs_root = ctx.get("ui_prefs") or {}
    pane = (prefs_root.get("panes", {}) or {}).get("cortex", {}) or {}

    settings = dict(DEFAULT_SETTINGS)
    for k in _SETTING_KEYS:
        if k in pane and pane[k] is not None:
            settings[k] = pane[k]
    try:
        settings["count"] = max(3, min(POOL_N, int(settings["count"])))
    except (TypeError, ValueError):
        settings["count"] = DEFAULT_N

    # Always load a pool by value; the client reorders/slices live.
    cards = select_cards(ctx.get("all_items") or [], n=POOL_N, picks=picks)
    cards = [c for c in cards if c.get("art")]
    if len(cards) < 3:
        return ('<div class="card cortex-card">'
                '<h3>🧠 Cortex</h3>'
                '<div class="hint" style="padding:18px;text-align:center;'
                'color:var(--muted)">Add a few priced cards with art and your '
                'collection\'s mind will take shape.</div></div>')

    from cc_cortex_looks import render_flow_card  # noqa: PLC0415
    return render_flow_card(cards, CORTEX_MESH_URL, settings)
