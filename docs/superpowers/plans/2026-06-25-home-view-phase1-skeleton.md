# Home View (Xbox-style) — Phase 1: Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a third launcher view `home` (Xbox-app-style: left rail + focus-reflecting hero banner + horizontal shelves), selectable in Settings and default on, with full gamepad navigation — no animations, no new persisted data yet.

**Architecture:** A new `joypad/ui/views/home/` package mirrors the existing `tiles/` package (pure `model.py` + `geometry.py`, focus logic in `navigation.py`, pixels in `drawing.py`). It plugs into the same `state.ui_mode` seam already used by `list`/`tiles`: `draw_frame` dispatches on it, and `joypad/ui/views/list/dispatch.py` routes navigation. Shelves are built from the existing `state.tile_sections` plus a synthetic "All (A–Z)" shelf. The stable per-game key reuses the existing `game_cache_key`.

**Tech Stack:** Python 3.8+, pygame, pytest. No new dependencies.

## Global Constraints

- **Python floor:** 3.8+ — no `match`, no `|` union types at runtime in new modules (the codebase uses `from __future__ import annotations` for annotations only).
- **No new third-party deps.** pygame + stdlib only.
- **Original colors only.** Use the theme's existing `highlight_color`/`text_color`/`title_color`/`bg_color`; do NOT hardcode Xbox green. A teal accent, if any new color is needed, comes from `state.highlight_color`.
- **Follow existing patterns:** dict-based geometry (like `tiles/geometry.py`), pure functions for testable logic, golden tests under `tests/test_*_golden.py` run via the project `.venv` (no system pip; see memory `dev-env-no-system-pip`).
- **pygame import guard:** rendering code must tolerate `pygame is None` only where the codebase already does; new pure modules must NOT import pygame.
- **Commit message style:** match the repo convention `[type] Capitalized imperative summary` (e.g. `[feat] Add home-view geometry`), NOT Conventional Commits `feat: …`. End each commit body with the `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` trailer.

---

### Task 1: `ui_mode` plumbing for "home"

Extend the three-way nature of the view setting so `home` is a recognized, default, cyclable mode.

**Files:**
- Modify: `joypad/config/theme/ui.py`
- Modify: `joypad/config/settings/toggle.py:33-35`
- Test: `tests/test_home_ui_mode.py` (create)

**Interfaces:**
- Produces: `ui_mode_from_theme(theme) -> "home"|"tiles"|"list"` (default now `"home"`); `ui_mode_label(mode) -> str`; toggle of key `"ui_mode"` cycles `home → tiles → list → home`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_home_ui_mode.py
from joypad.config.theme.ui import ui_mode_from_theme, ui_mode_label
from joypad.config.settings.toggle import apply_setting_toggle


def test_default_mode_is_home():
    assert ui_mode_from_theme({}) == "home"
    assert ui_mode_from_theme(None) == "home"


def test_explicit_modes_recognized():
    assert ui_mode_from_theme({"ui_mode": "home"}) == "home"
    assert ui_mode_from_theme({"ui_mode": "tiles"}) == "tiles"
    assert ui_mode_from_theme({"ui_mode": "list"}) == "list"


def test_label():
    assert ui_mode_label("home") == "Home"
    assert ui_mode_label("tiles") == "Tiles"
    assert ui_mode_label("list") == "List"


def test_toggle_cycles_home_tiles_list(tmp_path, monkeypatch):
    import joypad.config.settings.toggle as tg
    monkeypatch.setattr(tg, "save_config", lambda cfg: None)
    cfg = {"theme": {"ui_mode": "home"}}
    apply_setting_toggle(cfg, "ui_mode")
    assert cfg["theme"]["ui_mode"] == "tiles"
    apply_setting_toggle(cfg, "ui_mode")
    assert cfg["theme"]["ui_mode"] == "list"
    apply_setting_toggle(cfg, "ui_mode")
    assert cfg["theme"]["ui_mode"] == "home"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_home_ui_mode.py -v`
Expected: FAIL (default is `"list"`, label has no "Home", toggle only flips list/tiles).

- [ ] **Step 3: Implement — theme helpers**

```python
# joypad/config/theme/ui.py  (replace ui_mode_from_theme and ui_mode_label)
_UI_MODES = ("home", "tiles", "list")


def ui_mode_from_theme(theme_section):
    v = (theme_section or {}).get("ui_mode")
    if isinstance(v, str):
        s = v.strip().lower()
        if s in _UI_MODES:
            return s
    return "home"


def ui_mode_label(mode):
    return {"home": "Home", "tiles": "Tiles", "list": "List"}.get(mode, "Home")
```

- [ ] **Step 4: Implement — toggle cycle**

```python
# joypad/config/settings/toggle.py  (replace the ui_mode branch, lines ~33-35)
    elif key == "ui_mode":
        theme = config.setdefault("theme", {})
        order = ["home", "tiles", "list"]
        cur = ui_mode_from_theme(theme)
        theme["ui_mode"] = order[(order.index(cur) + 1) % len(order)]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_home_ui_mode.py tests/test_theme_golden.py tests/test_settings_golden.py -v`
Expected: PASS (and existing theme/settings golden tests still green).

- [ ] **Step 6: Commit**

```bash
git add joypad/config/theme/ui.py joypad/config/settings/toggle.py tests/test_home_ui_mode.py
git commit -m "[feat] Recognize and default to 'home' ui_mode"
```

---

### Task 2: `home/model.py` — build shelves

Build the ordered shelf list from existing sections plus an "All (A–Z)" shelf.

**Files:**
- Create: `joypad/ui/views/home/__init__.py`
- Create: `joypad/ui/views/home/model.py`
- Test: `tests/test_home_model_golden.py` (create)

**Interfaces:**
- Consumes: `state.tile_sections` shape `[{"title": str, "games": [game_dict]}]`.
- Produces: `build_home_shelves(tile_sections) -> [{"title": str, "games": list}]` — every non-empty source section in original order, then one `{"title": "All", "games": [...]}` shelf with all games sorted case-insensitively by `name`. Empty sections are dropped. If there are zero games, returns `[]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_home_model_golden.py
from joypad.ui.views.home.model import build_home_shelves


def _g(name, plat):
    return {"name": name, "platform": plat}


def test_shelves_are_sources_then_all():
    sections = [
        {"title": "Steam", "games": [_g("Hades", "steam"), _g("Celeste", "steam")]},
        {"title": "Epic Games", "games": [_g("Alan Wake", "epic")]},
    ]
    shelves = build_home_shelves(sections)
    assert [s["title"] for s in shelves] == ["Steam", "Epic Games", "All"]
    # "All" shelf sorted case-insensitively by name
    assert [g["name"] for g in shelves[-1]["games"]] == ["Alan Wake", "Celeste", "Hades"]


def test_empty_sections_dropped():
    sections = [
        {"title": "Steam", "games": []},
        {"title": "Epic Games", "games": [_g("Alan Wake", "epic")]},
    ]
    shelves = build_home_shelves(sections)
    assert [s["title"] for s in shelves] == ["Epic Games", "All"]


def test_no_games_returns_empty():
    assert build_home_shelves([{"title": "Steam", "games": []}]) == []
    assert build_home_shelves([]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_home_model_golden.py -v`
Expected: FAIL with `ModuleNotFoundError: joypad.ui.views.home`.

- [ ] **Step 3: Implement**

```python
# joypad/ui/views/home/__init__.py
"""Home view (Xbox-style): left rail + hero + horizontal shelves."""
```

```python
# joypad/ui/views/home/model.py
"""Build the ordered shelf list for the Home view."""


def build_home_shelves(tile_sections):
    """Source shelves (non-empty, original order) then an 'All' (A-Z) shelf."""
    shelves = []
    all_games = []
    for sec in tile_sections or []:
        games = sec.get("games") or []
        if not games:
            continue
        shelves.append({"title": sec["title"], "games": list(games)})
        all_games.extend(games)
    if not all_games:
        return []
    all_sorted = sorted(all_games, key=lambda g: (g.get("name") or "").lower())
    shelves.append({"title": "All", "games": all_sorted})
    return shelves
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_home_model_golden.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add joypad/ui/views/home/__init__.py joypad/ui/views/home/model.py tests/test_home_model_golden.py
git commit -m "[feat] Build home-view shelves from sections and All shelf"
```

---

### Task 3: `home/geometry.py` — rail/hero/shelf rectangles

Pure geometry, golden-testable like `tiles/geometry.py`.

**Files:**
- Create: `joypad/ui/views/home/geometry.py`
- Test: `tests/test_home_geometry_golden.py` (create)

**Interfaces:**
- Produces: `compute_home_geometry(w, h, hint_line_h, title_line_h) -> dict` with keys:
  `rail_w`, `content_x`, `margin`, `hero` (`{x,y,w,h}`), `shelf_area` (`{x,y,w,h}`),
  `tile_w`, `tile_h`, `tile_gap`, `shelf_label_h`, `shelf_stride`, `cover_w` (hero portrait), `cover_h`.
  Covers use a 2:3 portrait ratio (`tile_w = tile_h * 2 // 3`) to match Steam 600×900 art.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_home_geometry_golden.py
from joypad.ui.views.home.geometry import compute_home_geometry


def test_geometry_structure_and_bounds():
    g = compute_home_geometry(1280, 720, hint_line_h=26, title_line_h=52)
    assert g["rail_w"] == max(64, 1280 // 18)
    assert g["content_x"] == g["rail_w"]
    # hero sits right of the rail, inside margins
    assert g["hero"]["x"] >= g["rail_w"]
    assert g["hero"]["x"] + g["hero"]["w"] <= 1280
    # hero is roughly the top third-ish of the content height
    assert 0.30 <= g["hero"]["h"] / 720 <= 0.45
    # shelf area is below the hero and within the screen
    assert g["shelf_area"]["y"] >= g["hero"]["y"] + g["hero"]["h"]
    assert g["shelf_area"]["y"] + g["shelf_area"]["h"] <= 720
    # portrait tiles, 2:3
    assert g["tile_w"] == g["tile_h"] * 2 // 3
    assert g["shelf_stride"] == g["tile_h"] + g["shelf_label_h"] + g["tile_gap"]


def test_rail_minimum_on_small_screen():
    g = compute_home_geometry(640, 480, hint_line_h=20, title_line_h=42)
    assert g["rail_w"] == 64
    assert g["tile_h"] >= 48
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_home_geometry_golden.py -v`
Expected: FAIL with import error.

- [ ] **Step 3: Implement**

```python
# joypad/ui/views/home/geometry.py
"""Home view geometry: rail, hero, horizontal shelves. Pure (no pygame)."""


def compute_home_geometry(w, h, hint_line_h, title_line_h):
    rail_w = max(64, w // 18)
    margin = max(16, w // 60)
    content_x = rail_w
    content_w = w - rail_w

    top = max(24, title_line_h + 16)            # leave room for the screen title
    hero_h = int((h - top) * 0.38)
    hero = {
        "x": content_x + margin,
        "y": top,
        "w": content_w - 2 * margin,
        "h": hero_h,
    }

    shelf_y = hero["y"] + hero["h"] + margin
    shelf_area = {
        "x": content_x + margin,
        "y": shelf_y,
        "w": content_w - 2 * margin,
        "h": max(120, h - shelf_y - margin),
    }

    shelf_label_h = hint_line_h + 6
    tile_gap = max(8, w // 120)
    # Fit ~2 shelves of vertical space; tile height drives the rest.
    avail = shelf_area["h"]
    tile_h = max(48, int((avail - shelf_label_h - tile_gap) * 0.62))
    tile_w = tile_h * 2 // 3
    shelf_stride = tile_h + shelf_label_h + tile_gap

    # Hero portrait cover scaled to fit hero height with padding.
    cover_h = max(48, hero["h"] - 2 * margin)
    cover_w = cover_h * 2 // 3

    return {
        "rail_w": rail_w,
        "content_x": content_x,
        "margin": margin,
        "hero": hero,
        "shelf_area": shelf_area,
        "tile_w": tile_w,
        "tile_h": tile_h,
        "tile_gap": tile_gap,
        "shelf_label_h": shelf_label_h,
        "shelf_stride": shelf_stride,
        "cover_w": cover_w,
        "cover_h": cover_h,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_home_geometry_golden.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add joypad/ui/views/home/geometry.py tests/test_home_geometry_golden.py
git commit -m "[feat] Add home-view geometry (rail/hero/shelves)"
```

---

### Task 4: `home/navigation.py` — focus init + selected game

Introduce the focus model and the two read helpers other code needs.

**Files:**
- Create: `joypad/ui/views/home/navigation.py`
- Modify: `joypad/app_state.py` (add `home_shelves`, `home_focus`, `home_geom` fields)
- Test: `tests/test_home_navigation.py` (create)

**Interfaces:**
- Focus dict: `{"zone": "shelf"|"hero"|"rail", "shelf": int, "col": int, "rail": int}`.
- Produces:
  - `RAIL_ITEMS = ["home", "settings", "power"]`
  - `home_init_focus(state) -> None` — sets `state.home_focus`; zone `"shelf"` at `(0,0)` if shelves exist, else `"rail"` at index 0.
  - `home_selected_game(state) -> dict | None` — game under focus when zone is `"shelf"` or `"hero"`, else `None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_home_navigation.py
import types
from joypad.ui.views.home import navigation as nav


def _state(shelves):
    return types.SimpleNamespace(home_shelves=shelves, home_focus=None)


def _shelves():
    return [
        {"title": "Steam", "games": [{"name": "Hades"}, {"name": "Celeste"}]},
        {"title": "All", "games": [{"name": "Celeste"}, {"name": "Hades"}]},
    ]


def test_init_focus_first_tile():
    s = _state(_shelves())
    nav.home_init_focus(s)
    assert s.home_focus["zone"] == "shelf"
    assert s.home_focus["shelf"] == 0 and s.home_focus["col"] == 0


def test_init_focus_empty_goes_rail():
    s = _state([])
    nav.home_init_focus(s)
    assert s.home_focus["zone"] == "rail"


def test_selected_game_tracks_focus():
    s = _state(_shelves())
    nav.home_init_focus(s)
    assert nav.home_selected_game(s)["name"] == "Hades"
    s.home_focus["zone"] = "rail"
    assert nav.home_selected_game(s) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_home_navigation.py -v`
Expected: FAIL with import error.

- [ ] **Step 3: Implement state fields**

```python
# joypad/app_state.py  — add inside AppState, after the tile-view block (~line 34)
    # --- home-view geometry / focus ---
    home_geom: dict | None = None
    home_shelves: list | None = None
    home_focus: dict | None = None
```

- [ ] **Step 4: Implement navigation read helpers**

```python
# joypad/ui/views/home/navigation.py
"""Home view focus model and movement. Pure (no pygame)."""

RAIL_ITEMS = ["home", "settings", "power"]


def home_init_focus(state):
    if state.home_shelves:
        state.home_focus = {"zone": "shelf", "shelf": 0, "col": 0, "rail": 0}
    else:
        state.home_focus = {"zone": "rail", "shelf": 0, "col": 0, "rail": 0}


def _focused_shelf(state):
    shelves = state.home_shelves or []
    f = state.home_focus
    if not shelves or not f:
        return None
    return shelves[min(f["shelf"], len(shelves) - 1)]


def home_selected_game(state):
    f = state.home_focus
    if not f or f["zone"] not in ("shelf", "hero"):
        return None
    shelf = _focused_shelf(state)
    if not shelf or not shelf["games"]:
        return None
    col = min(f["col"], len(shelf["games"]) - 1)
    return shelf["games"][col]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_home_navigation.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add joypad/app_state.py joypad/ui/views/home/navigation.py tests/test_home_navigation.py
git commit -m "[feat] Add home-view focus model (init and selected game)"
```

---

### Task 5: `home/navigation.py` — movement transitions

Directional movement between shelves, hero, and rail, plus LB/RB shelf jumps.

**Files:**
- Modify: `joypad/ui/views/home/navigation.py`
- Test: `tests/test_home_navigation.py` (extend)

**Interfaces:**
- Consumes: focus dict and `RAIL_ITEMS` from Task 4.
- Produces:
  - `home_move(state, dx, dy) -> None` — mutates `state.home_focus`:
    - zone `shelf`: `dx<0` at `col==0` → zone `rail`; else `col` clamped `[0, len-1]`. `dy<0` at `shelf==0` → zone `hero`; else `shelf` clamped, `col` re-clamped to new shelf length.
    - zone `hero`: `dy>0` → zone `shelf`, `shelf=0`. `dx` ignored.
    - zone `rail`: `dy` moves `rail` clamped `[0, len(RAIL_ITEMS)-1]`; `dx>0` → zone `shelf` (return to content).
  - `home_lb_rb(state, delta) -> None` — move focused shelf by `delta` (same clamping as vertical `dy`), only when zone is `shelf`.

- [ ] **Step 1: Write the failing test (extend file)**

```python
# tests/test_home_navigation.py  (append)
def test_left_at_col0_enters_rail():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)
    assert s.home_focus["zone"] == "rail"


def test_right_within_shelf_then_left_back():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, 1, 0)
    assert s.home_focus["col"] == 1 and s.home_focus["zone"] == "shelf"
    nav.home_move(s, -1, 0)
    assert s.home_focus["col"] == 0 and s.home_focus["zone"] == "shelf"


def test_up_from_first_shelf_to_hero_and_back():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, 0, -1)
    assert s.home_focus["zone"] == "hero"
    nav.home_move(s, 0, 1)
    assert s.home_focus["zone"] == "shelf" and s.home_focus["shelf"] == 0


def test_down_clamps_col_to_new_shelf():
    s = _state([
        {"title": "A", "games": [{"name": "a"}, {"name": "b"}, {"name": "c"}]},
        {"title": "B", "games": [{"name": "x"}]},
    ])
    nav.home_init_focus(s)
    nav.home_move(s, 1, 0); nav.home_move(s, 1, 0)   # col=2
    nav.home_move(s, 0, 1)                            # down to shelf B (len 1)
    assert s.home_focus["shelf"] == 1 and s.home_focus["col"] == 0


def test_rail_right_returns_to_content():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)                # into rail
    nav.home_move(s, 0, 1)                 # move rail index down
    assert s.home_focus["rail"] == 1
    nav.home_move(s, 1, 0)                 # right -> back to content
    assert s.home_focus["zone"] == "shelf"


def test_lb_rb_moves_shelf():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_lb_rb(s, 1)
    assert s.home_focus["shelf"] == 1
    nav.home_lb_rb(s, -1)
    assert s.home_focus["shelf"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_home_navigation.py -v`
Expected: FAIL (`home_move`/`home_lb_rb` undefined).

- [ ] **Step 3: Implement**

```python
# joypad/ui/views/home/navigation.py  (append)

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _shelf_len(state, shelf_i):
    shelves = state.home_shelves or []
    if not shelves:
        return 0
    return len(shelves[_clamp(shelf_i, 0, len(shelves) - 1)]["games"])


def home_move(state, dx, dy):
    shelves = state.home_shelves or []
    f = state.home_focus
    if not f:
        home_init_focus(state)
        f = state.home_focus
    zone = f["zone"]

    if zone == "rail":
        if dy:
            f["rail"] = _clamp(f["rail"] + dy, 0, len(RAIL_ITEMS) - 1)
        if dx > 0:
            f["zone"] = "shelf" if shelves else "rail"
        return

    if zone == "hero":
        if dy > 0:
            f["zone"] = "shelf"
            f["shelf"] = 0
            f["col"] = _clamp(f["col"], 0, max(0, _shelf_len(state, 0) - 1))
        return

    # zone == "shelf"
    if dx < 0 and f["col"] == 0:
        f["zone"] = "rail"
        return
    if dx:
        f["col"] = _clamp(f["col"] + dx, 0, max(0, _shelf_len(state, f["shelf"]) - 1))
    if dy < 0 and f["shelf"] == 0:
        f["zone"] = "hero"
        return
    if dy:
        f["shelf"] = _clamp(f["shelf"] + dy, 0, max(0, len(shelves) - 1))
        f["col"] = _clamp(f["col"], 0, max(0, _shelf_len(state, f["shelf"]) - 1))


def home_lb_rb(state, delta):
    f = state.home_focus
    if f and f["zone"] == "shelf":
        home_move(state, 0, delta)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_home_navigation.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add joypad/ui/views/home/navigation.py tests/test_home_navigation.py
git commit -m "[feat] Add home-view directional movement and LB/RB"
```

---

### Task 6: `home/navigation.py` — confirm (A button) + rail activation

`A`/`Start`/`Enter` must launch when on a game, or activate a rail destination when in the rail.

**Files:**
- Modify: `joypad/ui/views/home/navigation.py`
- Test: `tests/test_home_navigation.py` (extend)

**Interfaces:**
- Consumes: focus dict, `RAIL_ITEMS`, `home_selected_game`.
- Produces: `home_confirm(state, on_launch) -> bool` — when zone is `shelf`/`hero`, calls `on_launch()` and returns its bool (True ⇒ app should exit/launch happened). When zone is `rail`, performs the destination action and returns `False`:
  - `"home"` → focus first shelf (`home_init_focus`).
  - `"settings"` → `state.overlay_menu = "settings"`, `state.overlay_index = 0`.
  - `"power"` → `state.overlay_menu = "system"`, `state.overlay_index = 0`.

- [ ] **Step 1: Write the failing test (extend file)**

```python
# tests/test_home_navigation.py  (append)
def _state_full(shelves):
    return types.SimpleNamespace(
        home_shelves=shelves, home_focus=None, overlay_menu=None, overlay_index=None
    )


def test_confirm_on_game_calls_launch():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    calls = []
    assert nav.home_confirm(s, lambda: calls.append(1) or True) is True
    assert calls == [1]


def test_confirm_rail_settings_opens_settings():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)                 # into rail (index 0 = home)
    nav.home_move(s, 0, 1)                  # index 1 = settings
    assert nav.home_confirm(s, lambda: True) is False
    assert s.overlay_menu == "settings" and s.overlay_index == 0


def test_confirm_rail_power_opens_system():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)
    nav.home_move(s, 0, 1); nav.home_move(s, 0, 1)   # index 2 = power
    assert nav.home_confirm(s, lambda: True) is False
    assert s.overlay_menu == "system"


def test_confirm_rail_home_focuses_content():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)                 # rail index 0 = home
    assert nav.home_confirm(s, lambda: True) is False
    assert s.home_focus["zone"] == "shelf"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_home_navigation.py -v`
Expected: FAIL (`home_confirm` undefined).

- [ ] **Step 3: Implement**

```python
# joypad/ui/views/home/navigation.py  (append)

def home_confirm(state, on_launch):
    f = state.home_focus
    if not f:
        return False
    if f["zone"] in ("shelf", "hero"):
        return bool(on_launch())
    # zone == "rail"
    dest = RAIL_ITEMS[_clamp(f["rail"], 0, len(RAIL_ITEMS) - 1)]
    if dest == "home":
        home_init_focus(state)
    elif dest == "settings":
        state.overlay_menu = "settings"
        state.overlay_index = 0
    elif dest == "power":
        state.overlay_menu = "system"
        state.overlay_index = 0
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_home_navigation.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add joypad/ui/views/home/navigation.py tests/test_home_navigation.py
git commit -m "[feat] Add home-view confirm and rail activation"
```

---

### Task 7: `home/drawing.py` — render rail, hero, shelves

Pixels. Hard to assert exact output, so the test is a headless smoke test: it must render without raising and blit something.

**Files:**
- Create: `joypad/ui/views/home/drawing.py`
- Modify: `joypad/ui/views/home/__init__.py` (export `draw_home_view`, navigation, `build_home_shelves`, `rebuild_home`)
- Test: `tests/test_home_drawing_smoke.py` (create)

**Interfaces:**
- Consumes: `state.home_geom`, `state.home_shelves`, `state.home_focus`, `state.cover_cache`, fonts (`font_title`, `font_category`, `font_hint`), colors, `state.screen`, `state.w/h`.
- Produces:
  - `rebuild_home(state) -> None` — rebuild `state.home_shelves` and `state.home_geom`, and init focus if missing.
  - `draw_home_view(state) -> None` — draw the whole view onto `state.screen`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_home_drawing_smoke.py
import os
import types
import pygame
import pytest

from joypad.ui.views.home.geometry import compute_home_geometry
from joypad.ui.views.home import navigation as nav


class _Cover:
    def get(self, game, w, h):
        s = pygame.Surface((w, h))
        s.fill((40, 40, 60))
        return s


def _fonts():
    pygame.font.init()
    return pygame.font.Font(None, 28)


@pytest.fixture
def headless_state():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    screen = pygame.Surface((1280, 720))
    f = _fonts()
    shelves = [
        {"title": "Steam", "games": [{"name": "Hades"}, {"name": "Celeste"}]},
        {"title": "All", "games": [{"name": "Celeste"}, {"name": "Hades"}]},
    ]
    st = types.SimpleNamespace(
        screen=screen, w=1280, h=720,
        home_shelves=shelves, home_focus=None, home_geom=None,
        cover_cache=_Cover(),
        font_title=f, font_category=f, font_hint=f,
        text_color=(230, 230, 230), title_color=(170, 170, 190),
        highlight_color=(45, 212, 191), bg_color=(20, 20, 28),
    )
    st.home_geom = compute_home_geometry(1280, 720, 26, 52)
    nav.home_init_focus(st)
    return st


def test_draw_home_view_runs(headless_state):
    from joypad.ui.views.home.drawing import draw_home_view
    draw_home_view(headless_state)   # must not raise


def test_draw_home_view_empty_shelves(headless_state):
    from joypad.ui.views.home.drawing import draw_home_view
    headless_state.home_shelves = []
    nav.home_init_focus(headless_state)
    draw_home_view(headless_state)   # must not raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest tests/test_home_drawing_smoke.py -v`
Expected: FAIL with import error for `draw_home_view`.

- [ ] **Step 3: Implement drawing**

```python
# joypad/ui/views/home/drawing.py
"""Home view pygame rendering: rail, hero, horizontal shelves."""

import pygame

from joypad.ui.views.home.geometry import compute_home_geometry
from joypad.ui.views.home.model import build_home_shelves
from joypad.ui.views.home.navigation import (
    RAIL_ITEMS,
    home_init_focus,
    home_selected_game,
)

_RAIL_GLYPH = {"home": "⌂", "settings": "⚙", "power": "⏻"}


def rebuild_home(state):
    state.home_shelves = build_home_shelves(state.tile_sections)
    state.home_geom = compute_home_geometry(
        state.w, state.h, state.font_hint.get_linesize(), state.font_title.get_linesize()
    )
    if not state.home_focus:
        home_init_focus(state)


def _truncate(font, text, max_w):
    t = (text or "").strip() or "Untitled"
    if font.size(t)[0] <= max_w:
        return t
    for n in range(len(t), 0, -1):
        if font.size(t[:n] + "…")[0] <= max_w:
            return t[:n] + "…"
    return "…"


def _draw_rail(state, g):
    f = state.home_focus
    rail_w = g["rail_w"]
    pygame.draw.rect(state.screen, (0, 0, 0), (0, 0, rail_w, state.h))
    n = len(RAIL_ITEMS)
    step = state.h // (n + 1)
    for i, item in enumerate(RAIL_ITEMS):
        cy = step * (i + 1)
        active = f and f["zone"] == "rail" and f["rail"] == i
        color = state.highlight_color if active else state.title_color
        glyph = state.font_title.render(_RAIL_GLYPH.get(item, "?"), True, color)
        rect = glyph.get_rect(center=(rail_w // 2, cy))
        if active:
            pygame.draw.rect(state.screen, state.highlight_color,
                             (4, cy - step // 2 + 6, rail_w - 8, step - 12), 2)
        state.screen.blit(glyph, rect)


def _draw_hero(state, g):
    hero = g["hero"]
    game = home_selected_game(state)
    pygame.draw.rect(state.screen, (30, 30, 42), (hero["x"], hero["y"], hero["w"], hero["h"]))
    if game is None:
        return
    # Blurred backdrop: scale cover up then down (cheap blur), tint dark.
    backdrop = state.cover_cache.get(game, hero["w"], hero["h"])
    if backdrop:
        small = pygame.transform.smoothscale(backdrop, (max(1, hero["w"] // 12), max(1, hero["h"] // 12)))
        blurred = pygame.transform.smoothscale(small, (hero["w"], hero["h"]))
        blurred.set_alpha(110)
        state.screen.blit(blurred, (hero["x"], hero["y"]))
    # Portrait cover, left.
    cover = state.cover_cache.get(game, g["cover_w"], g["cover_h"])
    cx = hero["x"] + g["margin"]
    cy = hero["y"] + (hero["h"] - g["cover_h"]) // 2
    if cover:
        state.screen.blit(cover, (cx, cy))
    # Text block, right of cover.
    tx = cx + g["cover_w"] + g["margin"]
    tw = hero["x"] + hero["w"] - tx - g["margin"]
    name = _truncate(state.font_title, game.get("name", ""), tw)
    state.screen.blit(state.font_title.render(name, True, state.text_color), (tx, cy))
    sub = _truncate(state.font_hint, (game.get("platform") or "").title(), tw)
    state.screen.blit(state.font_hint.render(sub, True, state.title_color),
                      (tx, cy + state.font_title.get_linesize() + 6))
    hint_y = cy + state.font_title.get_linesize() + state.font_hint.get_linesize() + 16
    play = state.font_hint.render("▶ Launch  (A)", True, state.highlight_color)
    state.screen.blit(play, (tx, hint_y))


def _draw_shelves(state, g):
    f = state.home_focus
    area = g["shelf_area"]
    prev_clip = state.screen.get_clip()
    state.screen.set_clip(pygame.Rect(area["x"], area["y"], area["w"], area["h"]))
    try:
        focus_shelf = f["shelf"] if f else 0
        # Scroll so the focused shelf is the first one drawn.
        y = area["y"] - focus_shelf * g["shelf_stride"]
        for si, shelf in enumerate(state.home_shelves or []):
            if y + g["shelf_stride"] >= area["y"] and y <= area["y"] + area["h"]:
                state.screen.blit(
                    state.font_category.render(shelf["title"], True, state.title_color),
                    (area["x"], y),
                )
                ty = y + g["shelf_label_h"]
                focus_col = f["col"] if (f and f["zone"] == "shelf" and f["shelf"] == si) else -1
                start = max(0, focus_col)  # keep focused tile visible by scrolling row
                x = area["x"]
                for ci in range(start, len(shelf["games"])):
                    if x > area["x"] + area["w"]:
                        break
                    cover = state.cover_cache.get(shelf["games"][ci], g["tile_w"], g["tile_h"])
                    if cover:
                        state.screen.blit(cover, (x, ty))
                    if ci == focus_col and f and f["zone"] == "shelf":
                        pygame.draw.rect(state.screen, state.highlight_color,
                                         (x - 3, ty - 3, g["tile_w"] + 6, g["tile_h"] + 6), 4)
                    x += g["tile_w"] + g["tile_gap"]
            y += g["shelf_stride"]
    finally:
        state.screen.set_clip(prev_clip)


def draw_home_view(state):
    g = state.home_geom
    if not g:
        rebuild_home(state)
        g = state.home_geom
    _draw_hero(state, g)
    _draw_shelves(state, g)
    _draw_rail(state, g)
```

- [ ] **Step 4: Export from package**

```python
# joypad/ui/views/home/__init__.py  (replace)
"""Home view (Xbox-style): left rail + hero + horizontal shelves."""

from joypad.ui.views.home.drawing import draw_home_view, rebuild_home
from joypad.ui.views.home.model import build_home_shelves
from joypad.ui.views.home.navigation import (
    home_confirm,
    home_init_focus,
    home_lb_rb,
    home_move,
    home_selected_game,
)

__all__ = [
    "build_home_shelves",
    "draw_home_view",
    "home_confirm",
    "home_init_focus",
    "home_lb_rb",
    "home_move",
    "home_selected_game",
    "rebuild_home",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest tests/test_home_drawing_smoke.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add joypad/ui/views/home/drawing.py joypad/ui/views/home/__init__.py tests/test_home_drawing_smoke.py
git commit -m "[feat] Add home-view rendering (rail/hero/shelves)"
```

---

### Task 8: Wire `home` into the loop, dispatch, and bootstrap

Connect rendering, navigation routing, the A-button, and startup so the view is live end to end.

**Files:**
- Modify: `joypad/ui/loop/frame.py:16-31`
- Modify: `joypad/ui/views/list/dispatch.py` (add home branches)
- Modify: `joypad/ui/loop/events/dispatch.py` (A/Start/Enter for home)
- Modify: `joypad/bootstrap/display.py` (build home in `init_fonts_and_layouts`)
- Test: `tests/test_home_integration.py` (create)

**Interfaces:**
- Consumes: `home.draw_home_view`, `home.rebuild_home`, `home.home_move`, `home.home_lb_rb`, `home.home_confirm`, `home.home_selected_game`.
- Produces: with `state.ui_mode == "home"`, `draw_frame` renders the home view; `nav_vertical/nav_horizontal/nav_page/nav_lb_rb` and `get_selected_item` route to home; `A`/`Start`/`Enter` call `home_confirm`.

- [ ] **Step 1: Write the failing integration test**

```python
# tests/test_home_integration.py
import types
import joypad.ui.views.list.dispatch as disp


def _home_state():
    shelves = [
        {"title": "Steam", "games": [{"name": "Hades"}, {"name": "Celeste"}]},
        {"title": "All", "games": [{"name": "Celeste"}, {"name": "Hades"}]},
    ]
    from joypad.ui.views.home.navigation import home_init_focus
    st = types.SimpleNamespace(ui_mode="home", home_shelves=shelves, home_focus=None)
    home_init_focus(st)
    return st


def test_dispatch_routes_to_home():
    s = _home_state()
    disp.nav_horizontal(s, 1)
    assert s.home_focus["col"] == 1
    disp.nav_vertical(s, -1)
    assert s.home_focus["zone"] == "hero"


def test_get_selected_item_home():
    s = _home_state()
    item = disp.get_selected_item(s)
    assert item == {"kind": "game", "game": {"name": "Hades"}}


def test_nav_lb_rb_home_moves_shelf():
    s = _home_state()
    disp.nav_lb_rb(s, 1)
    assert s.home_focus["shelf"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_home_integration.py -v`
Expected: FAIL (dispatch has no home branch; `home_focus` unchanged / wrong item).

- [ ] **Step 3: Route navigation in `list/dispatch.py`**

```python
# joypad/ui/views/list/dispatch.py  (replace whole file)
"""Unified navigation dispatch (list vs tiles vs home)."""

from joypad.ui.views import home, tiles
from joypad.ui.views.list.navigation import move_game_selection, page_scroll


def get_selected_item(state):
    if state.ui_mode == "home":
        g = home.home_selected_game(state)
        return {"kind": "game", "game": g} if g is not None else None
    if state.ui_mode == "tiles":
        g = tiles.tile_selected_game(state)
        return {"kind": "game", "game": g} if g is not None else None
    if 0 <= state.selected < len(state.list_items) and state.list_items[state.selected]["kind"] == "game":
        return state.list_items[state.selected]
    return None


def nav_vertical(state, delta):
    if state.ui_mode == "home":
        home.home_move(state, 0, delta)
    elif state.ui_mode == "tiles":
        tiles.tile_move(state, 0, delta)
    else:
        move_game_selection(state, delta)


def nav_horizontal(state, delta):
    if state.ui_mode == "home":
        home.home_move(state, delta, 0)
    elif state.ui_mode == "tiles":
        tiles.tile_move(state, delta, 0)


def nav_page(state, delta):
    if state.ui_mode == "home":
        home.home_lb_rb(state, delta)
    elif state.ui_mode == "tiles":
        tiles.tile_page_scroll(state, delta)
    else:
        page_scroll(state, delta)


def nav_lb_rb(state, delta):
    if state.ui_mode == "home":
        home.home_lb_rb(state, delta)
    elif state.ui_mode == "tiles":
        _sec_i, local = tiles._tile_pick_location(state, state.tile_pick)
        if local == 0:
            tiles.tile_section_jump(state, delta)
        else:
            tiles.tile_page_scroll(state, delta)
    else:
        page_scroll(state, delta)
```

- [ ] **Step 4: Run dispatch tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_home_integration.py -v`
Expected: PASS.

- [ ] **Step 5: Render home in `frame.py`**

```python
# joypad/ui/loop/frame.py  (replace draw_frame body and update_scroll)
import pygame

from joypad.ui import overlay as ovl
from joypad.ui.views import home as hm
from joypad.ui.views import list as lst
from joypad.ui.views import tiles


def update_scroll(state) -> None:
    if state.ui_mode == "tiles" and state.tile_snap_scroll:
        tiles._tile_snap_scroll(state)
    lst.snap_list_scroll(state)


def draw_frame(state) -> None:
    screen = state.screen
    h = state.h
    screen.fill(state.bg_color)
    if state.bg_surface and state.ui_mode != "home":
        screen.blit(state.bg_surface, (0, 0))
    screen.blit(state.title_surface, (60, 40))

    if state.ui_mode == "home":
        hm.draw_home_view(state)
    elif state.ui_mode == "tiles":
        screen.blit(state.hint_surface, (60, h - state.tile_geom["bottom_hint"]))
        tiles.draw_tiles_view(state)
    else:
        screen.blit(state.hint_surface, (60, h - state.list_bottom_margin))
        lst.draw_list_view(state)

    ovl.draw_overlay(state)
    pygame.display.flip()
```

- [ ] **Step 6: Wire the A button for home in `events/dispatch.py`**

In `joypad/ui/loop/events/dispatch.py`, replace the keyboard Enter handler (the `if event.key == pygame.K_RETURN:` block at lines ~72-75) and the gamepad A/Start handler (the `if btn == BTN_A or btn == BTN_START:` block at lines ~96-99, the non-overlay branch) so home routes through `home_confirm`:

```python
# add import near the top (with the other view imports)
from joypad.ui.views import home as hm

# keyboard, non-overlay RETURN (replace existing block):
                if event.key == pygame.K_RETURN:
                    launched = hm.home_confirm(state, on_launch) if state.ui_mode == "home" else on_launch()
                    if launched:
                        state.running = False
                        return joysticks, True

# gamepad, non-overlay A/START (replace existing block):
                if btn == BTN_A or btn == BTN_START:
                    launched = hm.home_confirm(state, on_launch) if state.ui_mode == "home" else on_launch()
                    if launched:
                        state.running = False
                        return joysticks, True
                elif btn == BTN_LB:
                    lst.nav_lb_rb(state, -1)
                elif btn == BTN_RB:
                    lst.nav_lb_rb(state, 1)
```

- [ ] **Step 7: Build home state at startup in `bootstrap/display.py`**

In `init_fonts_and_layouts` (where tile geometry is already rebuilt), add a home rebuild so the view is ready regardless of the saved `ui_mode` (cheap; lets runtime view-switching work). Add at the end of that function:

```python
    from joypad.ui.views.home import rebuild_home
    rebuild_home(state)
```

(If `init_fonts_and_layouts` does not currently import or rebuild tile geometry, place this call right after `rebuild_tile_geometry(state)` wherever that occurs during bootstrap; grep `rebuild_tile_geometry` to confirm the exact site.)

- [ ] **Step 8: Run the full suite**

Run: `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q`
Expected: PASS (all existing tests plus the new home tests).

- [ ] **Step 9: Manual smoke (optional but recommended)**

Run: `.venv/bin/python launcher.py` with `"ui_mode": "home"` in `config.json` theme. Verify: rail on the left, hero reflects the focused game, shelves scroll, Left-at-edge enters the rail, A launches, B opens the system menu.

- [ ] **Step 10: Commit**

```bash
git add joypad/ui/loop/frame.py joypad/ui/views/list/dispatch.py \
        joypad/ui/loop/events/dispatch.py joypad/bootstrap/display.py \
        tests/test_home_integration.py
git commit -m "[feat] Wire home view into loop, dispatch, and bootstrap"
```

---

## Phase 1 Done — what ships

A working `home` view: left rail (Home / Settings / Power), hero banner that reflects the focused game (portrait cover + cheap blurred backdrop + Launch hint), and horizontal source shelves plus an "All" shelf. Full gamepad navigation per the spec, A launches, B opens the system menu, Settings → Appearance → View cycles Home / Tiles / List. No animations, no persisted state.

## Follow-up plans (separate specs already approved)

- **Phase 2 — Animations:** delta-time render, exponential-smoothing tween helpers (`animation.py`), sliding selection highlight, focused-tile scale, smooth horizontal/vertical scroll, hero crossfade, rail expansion. Will get its own plan: `docs/superpowers/plans/<date>-home-view-phase2-animations.md`.
- **Phase 3 — Persistence:** `joypad/state/library_state.py` (JSON next to config), "Recently" + "Favorites" shelves, `Y` toggles favorite (verify/add `BTN_Y` in `joypad/input/constants.py`), record `last_played` on launch, source icons in the rail as quick filters. Own plan.

## Self-Review notes

- Spec coverage: rail ✓ (Task 7), hero-reflects-focus ✓ (Tasks 4/7), shelves from sources + All ✓ (Task 2), navigation incl. edge-to-rail + LB/RB ✓ (Tasks 5/6/8), default+toggle ✓ (Task 1), tests by golden pattern ✓. Animations & Recently/Favorites deferred to Phase 2/3 by design.
- Type consistency: focus dict keys (`zone/shelf/col/rail`) and function names (`home_move/home_lb_rb/home_confirm/home_selected_game/home_init_focus/rebuild_home/build_home_shelves`) are used identically across tasks and the `__init__` exports.
- Reused stable key: shelves carry raw game dicts; `cover_cache.get` already derives `game_cache_key` internally, so Phase 1 needs no new key (the `game_key` helper is deferred to Phase 3 where favorites need it).
