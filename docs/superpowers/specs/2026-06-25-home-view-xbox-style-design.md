# Design: «Home» view (Xbox-style) for Joypad Launcher

**Date:** 2026-06-25
**Status:** Approved (design), pending implementation plan

## Goal

Add a third launcher view, `home`, whose layout and navigation evoke the Windows
Xbox app — left navigation rail, a focus-reflecting hero banner, and horizontal
shelves of cover art — adapted for **gamepad-only** use. Colors are original
(teal accent, not Xbox green); only the **layout and behavior** are similar.

`home` becomes the default view. The existing `list` and `tiles` views remain,
selectable in **Settings → Appearance → View**. Nothing in the current views is
removed.

## Non-goals

- Acrylic/Mica true background blur of the OS desktop (pygame can't cheaply do
  it). We fake depth with a pre-blurred cover backdrop inside the hero only.
- Replacing or reworking `list`/`tiles`.
- Online/store/social features. This stays a thin launcher shell.

## Architecture and integration

View selection already flows through `state.ui_mode` (`"tiles"` | `"list"`);
`joypad/ui/loop/frame.py:draw_frame` dispatches on it, and sections already exist
as `state.tile_sections` (`[{"title", "games"}]`). The new view slots into this
seam.

- Add `ui_mode == "home"` branch to `draw_frame` (and to `update_scroll`).
- New package `joypad/ui/views/home/` mirroring `joypad/ui/views/tiles/`:
  - `geometry.py` — rail / hero / shelf rectangles and tile sizing. Pure,
    golden-testable like `tiles/geometry.py`.
  - `model.py` — build `home_shelves` from `tile_sections` plus synthetic
    "Recently" and "Favorites" shelves (Phase 3).
  - `drawing.py` — render rail, hero, shelves.
  - `navigation.py` — focus model (zone + indices) and transitions, like
    `tiles/navigation/`.
  - `animation.py` — pure tween/easing helpers.
  - `__init__.py` — public surface (`draw_home_view`, navigation entry points).

### AppState additions

New fields on `joypad/app_state.py:AppState`:

- `home_geom: dict | None` — rail/hero/shelf geometry (rebuilt on resize).
- `home_shelves: list | None` — `[{"title", "games"}]`, ordered.
- `home_focus: dict | None` — `{"zone": "shelf"|"hero"|"rail", "shelf": int,
  "col": int, "rail": int}`.
- `home_anim: dict | None` — current/target animated values (selection rect,
  per-shelf `scroll_x`, vertical `scroll_y`, hero crossfade alpha, tile scale,
  rail expansion).

### Stable game key

Favorites and Recently need a stable id per game. Add
`game_key(game) -> str` (in `joypad/games/model.py`): `platform` joined with the
first present of `appid` / `nsp_path` / `exe` / `name`. Exact id field names are
verified against `joypad/games/scan.py` during implementation.

## Layout and geometry

```
┌────┬──────────────────────────────────────────────┐
│ ◆  │  ╔══════════════════════════════════════════╗ │
│ ⌂  │  ║ [blurred cover backdrop]                  ║ │  HERO (~38% of
│ ─  │  ║  ┌──┐  CYBERPUNK 2077                     ║ │  content height),
│ ⓢ │  ║  │▓▓│  Steam · ▶ Launch (A)               ║ │  reflects focus
│ ⓔ │  ║  └──┘  ★ Favorite (Y)                     ║ │
│ ─  │  ╚══════════════════════════════════════════╝ │
│ ⚙  │  Recently                                     │  SHELVES:
│ ⏻  │  ┏━━┓ ╭──╮ ╭──╮ ╭──╮ ╭──╮  →                  │  focused shelf shown
│    │  ┗━━┛ ╰──╯ ╰──╯ ╰──╯ ╰──╯                     │  fully; neighbors peek
│    │  Steam                                        │
│    │  ╭──╮ ╭──╮ ╭──╮ …                             │
└────┴──────────────────────────────────────────────┘
```

- **Rail**: fixed width `max(64, w // 18)`, full height. Icons top-to-bottom:
  Home, divider, one icon per detected source (Steam / Epic / Twitch / Other),
  divider, Settings, Power. Active item drawn with the teal accent. On focus,
  the rail expands slightly to reveal text labels (Phase 2 animation).
- **Hero**: top of the content area. A pre-blurred, enlarged cover fills the
  background; the portrait cover sits left; title, source badge, and the A/Y
  hint lines sit right. The blurred backdrop and scaled cover are computed
  **once per focused game and cached** — never per frame.
- **Shelves**: each is a label plus a horizontal row of covers from
  `state.cover_cache.get(game, tw, th)`. Only the focused shelf is fully
  visible; adjacent shelves peek to signal vertical scrolling. Within a shelf,
  off-screen tiles to the right are clipped and reachable by horizontal scroll.

Geometry is recomputed on resize (mirrors `rebuild_tile_geometry`).

## Gamepad navigation

Focus zones: **SHELF** (a tile within a shelf), **HERO** (the Launch button),
**RAIL** (a rail destination).

- Default focus on entry: first tile of the first shelf; hero reflects it.
- **Left / Right**: move within the focused shelf; hero updates to the focused
  game.
- **Up** from the first shelf → HERO (Launch button); **Down** → next shelf.
- **Up** from HERO stays on HERO. **Down** from the last shelf stays.
- **Left** on column 0 of a shelf → RAIL (Xbox edge behavior).
- In **RAIL**: Up/Down move between destinations; **Right** returns to content
  (last focused shelf/col); **A** activates the destination — Home (focus first
  shelf), a source (jump focus to that source's shelf), Settings (open settings
  overlay), Power (open system menu).
- **LB / RB**: quick-cycle rail destinations without entering the rail.
- **A**: launch focused game (SHELF or HERO) / activate destination (RAIL).
- **Start**: launch focused game (preserves current behavior).
- **B**: open the system menu (preserves current behavior).
- **Y**: toggle Favorite for the focused game (Phase 3).
- **LT / RT**: page vertically between shelves (fast vertical scroll).

## Smooth animations

The main loop renders every frame; add a continuous render with a delta-time
from `pygame.Clock`. All animations use frame-rate-independent exponential
smoothing: `cur += (target - cur) * (1 - exp(-k * dt))`. Helpers live in
`animation.py` as pure functions (deterministic given `dt`).

Animated quantities:

- **Selection highlight** — the highlight rect glides toward the focused tile
  rather than teleporting.
- **Focused tile scale** — 1.0 → 1.08 on focus.
- **Horizontal shelf scroll** — smooth lerp of the focused shelf's `scroll_x`.
- **Vertical scroll** — smooth lerp of `scroll_y` between shelves.
- **Hero crossfade** — on focus-game change, the old cover/backdrop fades out
  (alpha tween) while the new fades in; the blurred backdrop cross-dissolves.
- **Rail expansion** — icons widen / reveal labels on focus.

Performance: blur and scaled covers are cached per game; per frame only alpha
and positions change. Target a stable 60fps.

## Phasing

1. **Home skeleton** — `ui_mode == "home"` (default), rail (Home / Settings /
   Power) + static hero (reflects focus, no animation) + shelves from existing
   sources plus an "All (A–Z)" shelf; navigation per the section above; the
   Settings → Appearance → View toggle. No new persisted data, no animations.
2. **Animations** — tween helpers and everything in the animations section.
3. **Persistence** — `joypad/state/library_state.py` storing JSON next to
   `config.json` (`{"last_played": {key: ts}, "favorites": [key]}`); the
   "Recently" and "Favorites" shelves; **Y** toggles favorite; `last_played`
   recorded on launch; source icons in the rail act as quick filters/jumps.

## Testing

Following the existing golden-test pattern (`tests/test_*_golden.py`):

- **Geometry golden** — rail / hero / shelf rectangles and tile sizing for a few
  screen sizes and shelf counts.
- **Navigation unit tests** — focus transitions (shelf ↔ hero ↔ rail, edges,
  LB/RB cycling), mirroring the tile navigation tests.
- **Tween helpers** — pure-function tests, deterministic given `dt`.
- **Persistence store** (Phase 3) — load / save / toggle favorite / record
  launch, including missing-file and malformed-file handling.

## Open implementation details (resolved during build, not blocking)

- Exact id fields for `game_key` (confirm against `scan.py`).
- Whether the main loop is currently event-gated; if so, switch to continuous
  ticking for animations (Phase 2).
- Rail icon assets vs. drawn glyphs (start with drawn glyphs to avoid new
  asset dependencies).
