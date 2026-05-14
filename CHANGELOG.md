# Changelog

All user-visible changes to [cameraderiecards.com](https://cameraderiecards.com).
The actual source lives in a private repository — this changelog
summarizes what shipped in plain language.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

---

## Unreleased

_Things in flight but not yet live. Empty here means everything's deployed._

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
