# Changelog

All user-visible changes to [cameraderiecards.com](https://cameraderiecards.com).
The actual source lives in a private repository — this changelog
summarizes what shipped in plain language.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

---

## Unreleased

_Things in flight but not yet live. Empty here means everything's deployed._

---

## 2026-06-09 — Card Geode + open-source webcards

### Added
- 💎 **Card Geode** — a new art card. Your collection cracked open like a
  geode: in 3D, real quartz crystals grow inward from the rock cavity wall
  with a card mapped onto each crystal face; drag to orbit, scroll to zoom,
  click a crystal to view that card. Also a 2D agate-slice view. Gear:
  view, how many cards (top 10–250), crystal tint, glow, sparkle, spin.
- 🃏 **Open-source webcards** — the new [`webcards/`](webcards/) directory is
  MIT-licensed so the community can read, improve, and propose dashboard
  cards. The Card Geode is the first one published there. Code PRs welcome
  (see [`webcards/README.md`](webcards/README.md)).

### Fixed
- Sealed product photos now show with a transparent background everywhere
  (no more white box behind booster boxes).
- Site favicon (the gold "G") now displays in browser tabs/bookmarks.

---

## 2026-05-23 — Museum positioning + new art cards

### Added
- 🏛 **Champions' Podium** — a new art card. Your top five cards
  take the stage on carved-stone pedestals at podium heights
  (4-2-1-3-5 left to right), with gold trim and a crown badge on
  #1. Click any card to enter **exhibit mode** with an expanded
  curator's plaque (rank, share of collection, copies, acquisition
  date). The **▶ Begin ceremony** button auto-cycles through all
  five with a confetti burst.
- 🎴 **Card-of-Cards Mosaic** polish — settings panel closes
  cleanly when you click on the mosaic, the reveal image now fills
  the entire stage on guess/reveal, and the panel no longer
  persists across page loads.
- 👑 **Crown Jewel** completely rebuilt. Spinning faceted gem
  behind the card, sweeping conic light rays, drifting sparkles,
  floating-card animation, velvet vignette. Reads as a treasure on
  display instead of a list item.
- 📜 **Flavor Text Roulette** completely rebuilt as an *aged
  manuscript*: parchment background, illuminated card portrait in
  the corner, typewriter quill effect that reveals the quote
  character-by-character, and a red wax **CC** seal.

### Changed
- 🏛 **Museum-first default dashboard.** New users (and anyone who
  hits "↻ Reset Overview to default") now land on a 7-card canvas
  led by the art cards — Champions' Podium, Card-of-Cards Mosaic,
  Fibonacci Spiral, Woven Quilt — alongside the showcase widget,
  Story of You, and Wish Box. The data-heavy cards (Value by
  Category, Top 10, Badges, Value Horizon) remain available via
  **+ Add card** but no longer dominate the first impression.
- 📖 **Mission re-anchored as "a museum for your MTG
  collection."** Splash bullets, the "What is this?" panel, the
  Mission modal, and the meta + OG tags were all rewritten to lead
  with the museum/showcase positioning. CC now explicitly
  positions itself *alongside* Manabox / Moxfield / price
  aggregators instead of competing with them — "the room you take
  your finished collection into to show it off."
- 🏷 Login splash tagline: **"Your Magic collection, on display in
  a hundred ways."**
- 🌀 Landing carousel caption corrected: "Fibonacci spirals made
  of your cards" (was "Golden spirals of your top cards").
- 🟢 **Concurrent-viewer pill** now reflects a community-presence
  baseline (drifts realistically with time-of-day, range 18–200)
  plus the actual count of logged-in viewers. So the topbar always
  feels alive even at quiet hours, and real activity adds on top.

### Removed
- ⏳ **Time Travel showcase mode retired.** The 12 % CAGR-back
  projection chart didn't fit the museum positioning. Anyone whose
  saved widget was Time Travel auto-recovers to Crown Jewel.
- 📈 **Top Movers showcase mode retired.** Same reason — too
  trading-dashboard, not enough museum.

### Fixed
- The drawer's **↻ Reset Overview to default** button now actually
  resets to the current default (had a stale hardcoded layout that
  diverged from what the server thought was the default).
- Champions' Podium ceremony now leads with **#1** (was building
  bottom-up, which felt anticlimactic — the champion is the lede).

---

## 2026-05-13 — Dragon polish + landing page

### Added
- 🐉 **Three new fire sliders** in the dragon settings popup:
  *Fire range*, *Fire speed*, and *Fire spread (0–180°)*. Tune the
  dragon's breath without leaving the page.
- 🎨 **Nine colormaps** for the fire stream: Hot, Inferno, Magma,
  Plasma, Viridis, Cool, Acid, Frost, and Rainbow. Selecting one
  fires a preview burst.
- 🔥 **Hold Ctrl+F (or ⌘F) for continuous fire**. Press once for a
  single burst; hold for a stream.
- 💡 **Hint in the dragon settings popup** showing the Ctrl+F binding.
- 📖 **This public companion repo** at
  [github.com/rnorlund/cameraderie-cards](https://github.com/rnorlund/cameraderie-cards).
- ™ **Trademark mark established** — "Cameraderie Cards™" is now in
  use under common-law trademark in connection with the application.

### Changed
- 🪙 The "Guard the Hoard" / 🔒 "Cage the Beast" button now toggles
  the label correctly (was lowercase, now Title Case).
- The dashboard's ⌥ GitHub button now points to **this** repo instead
  of the private source repo, so anonymous visitors actually have a
  page to land on.

---

## 2026-05-10 — Initial production deploy

The eight-day build sprint that brought Cameraderie Cards from a
local pricing script to a multi-tenant, OAuth-authenticated,
subscription-billed web application.

- Live at [cameraderiecards.com](https://cameraderiecards.com) on
  Fly.io.
- 33 distinct dashboard card types — Sunburst by category, Top
  Movers, Foil Showcase, Watchlist, Set Completion, Diversity Score,
  Tournament Bracket, Auto-Cube Builder, and many more.
- Pack-cracking simulator with foil-aware sampling for draft and
  collector boosters, box toppers, and curated drops.
- Sign in with Google. Stripe Checkout for Pro Monthly and Lifetime
  tiers. Transactional email via Resend.
- Per-user collection isolation. Import from Excel, CSV, or Manabox
  exports.

For the full eight-day build write-up, see the project's build
summary (available on request).
