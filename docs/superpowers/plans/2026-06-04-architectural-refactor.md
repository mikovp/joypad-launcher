# Architectural Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the flat-file Joypad Launcher script into a layered `joypad/` Python package, isolating Windows OS code and splitting the two god-files, while preserving behavior 1:1.

**Architecture:** A `joypad/` package layered by responsibility (config, games, covers, launch, input, ui, platform). All ctypes/winreg/window/process code is gathered into `joypad/platform/windows.py`; pygame stays in `joypad/ui/` and `joypad/covers/cache.py`. `launcher.py` becomes a thin shim that calls `joypad.app.main(sys.argv)`, which routes the `--input-remap-worker` flag to the remap worker before starting pygame. The work proceeds leaf→core so imports always point "up", and `python launcher.py` stays runnable after every task.

**Tech Stack:** Python 3.8+, pygame, vdf, ctypes (Windows), pytest (dev only).

**Spec:** `docs/superpowers/specs/2026-06-04-architectural-refactor-design.md`

---

## Conventions used in this plan

- **VERBATIM MOVE** means: cut the named functions/constants from the source file and paste them into the target module *unchanged line-for-line*, editing ONLY the `import` lines and any cross-module references. No logic, formatting, or naming changes. Each such task ends with a diff check that must show only import/reference deltas.
- **Smoke run** = `python launcher.py` launches the UI without error on Windows (manual, by the user). On the dev box (Linux/CI) the equivalent automatic gate is: `python -c "import joypad, joypad.app"` imports cleanly and `pytest` is green. Note `pygame` and Windows modules may not import on the dev box — keep OS/pygame imports lazy (inside functions) exactly as the current code already does.
- Run `pytest` from the repo root. Run `python` from the repo root so `joypad` is importable.
- Commit after every task. Never leave the tree with `python -c "import joypad"` broken.

---

## File Structure

Files created/modified across the plan (responsibility in parentheses):

- `requirements-dev.txt` (create — pytest)
- `tests/conftest.py` (create — path + fixtures)
- `tests/test_theme_golden.py`, `tests/test_profiles_golden.py`, `tests/test_bindings_golden.py`, `tests/test_games_model_golden.py`, `tests/test_tile_grid_golden.py`, `tests/test_fonts_golden.py` (create — characterization)
- `tests/test_entry_dispatch.py` (create — worker-flag routing)
- `joypad/__init__.py`, `joypad/app.py` (create — package + entry/loop)
- `joypad/platform/windows.py` (create — OS isolation layer)
- `joypad/config/{loader,theme,settings}.py` (create)
- `joypad/games/{model,scan,scan_debug}.py` (create)
- `joypad/covers/{cache,cdn}.py` (create)
- `joypad/launch/launcher.py` (create)
- `joypad/input/{profiles,bindings,engine,watch,worker,log}.py` (create)
- `joypad/ui/{fonts,background,overlay,editor}.py`, `joypad/ui/views/{list,tiles}.py` (create)
- `launcher.py` (modify — becomes thin shim at the end)
- `build_exe.bat`, `.github/workflows/release.yml` (modify — packaging)
- Deleted at the end: `covers.py`, `cover_cdn.py`, `scan_libraries.py`, `scan_debug.py`, `input_remap.py`, `input_remap_editor.py` (contents relocated)

---

# Stage 1 — Scaffold + characterization safety net

Goal: stand up `joypad/` skeleton, `tests/`, and golden tests that pin current behavior of the pure logic — written against the **still-flat** modules. App still runs the old way.

### Task 1.1: Create dev requirements and test scaffolding

**Files:**
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest>=7.0
```

- [ ] **Step 2: Create `tests/conftest.py`** so tests can import the repo-root modules

```python
import os
import sys

# Repo root on sys.path so flat modules (launcher, input_remap, ...) and the
# joypad package are both importable during the migration.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
```

- [ ] **Step 3: Install dev deps**

Run: `pip install -r requirements-dev.txt`
Expected: pytest installed, no errors.

- [ ] **Step 4: Verify pytest collects nothing yet**

Run: `pytest -q`
Expected: "no tests ran" (exit code 5 is fine).

- [ ] **Step 5: Commit**

```bash
git add requirements-dev.txt tests/conftest.py
git commit -m "[test] Add pytest dev deps and test scaffolding"
```

### Task 1.2: Golden tests for theme/color parsing

**Files:**
- Test: `tests/test_theme_golden.py`

These import the still-flat `launcher` module. `launcher.py` only imports stdlib + pygame at top level; pygame must be importable on the dev box for this. If pygame is unavailable, install it (`pip install pygame`) — it is a runtime dependency already.

- [ ] **Step 1: Write the characterization test**

```python
import launcher


def test_parse_color_hex_six():
    assert launcher._parse_color("#1a2b3c", (0, 0, 0)) == (0x1a, 0x2b, 0x3c)


def test_parse_color_hex_short():
    assert launcher._parse_color("#fff", (0, 0, 0)) == (255, 255, 255)


def test_parse_color_list():
    assert launcher._parse_color([10, 20, 30], (0, 0, 0)) == (10, 20, 30)


def test_parse_color_invalid_returns_default():
    assert launcher._parse_color("zzz", (1, 2, 3)) == (1, 2, 3)
    assert launcher._parse_color(None, (4, 5, 6)) == (4, 5, 6)


def test_parse_font_size_clamps():
    assert launcher._parse_font_size(5, 28, 12, 72) == 12
    assert launcher._parse_font_size(999, 28, 12, 72) == 72
    assert launcher._parse_font_size("30", 28, 12, 72) == 30
    assert launcher._parse_font_size(None, 28) == 28


def test_parse_font_bold():
    assert launcher._parse_font_bold("bold") is True
    assert launcher._parse_font_bold("normal") is False
    assert launcher._parse_font_bold(None, True) is True


def test_theme_from_config_defaults_and_overrides():
    theme = launcher._theme_from_config(
        {"theme": {"background": "#14141c", "font_size_title": 50}}
    )
    assert theme["background"] == (0x14, 0x14, 0x1c)
    assert theme["font_size_title"] == 50
    # default applied when missing
    assert theme["text"] == launcher.TEXT_COLOR
    assert theme["font_size_list"] == 28
```

- [ ] **Step 2: Run to verify it passes against current code**

Run: `pytest tests/test_theme_golden.py -v`
Expected: PASS (this pins existing behavior; if any assert is wrong, correct the assert to match current output — do NOT change `launcher.py`).

- [ ] **Step 3: Commit**

```bash
git add tests/test_theme_golden.py
git commit -m "[test] Golden tests for theme/color parsing"
```

### Task 1.3: Golden tests for input-profile notation round-trip

**Files:**
- Test: `tests/test_profiles_golden.py`

- [ ] **Step 1: Write the test using the real shipped profile**

```python
import json
import os

import input_remap

PROFILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "input_profiles",
    "default_wasd_mouse.json",
)


def _load():
    with open(PROFILE, encoding="utf-8") as f:
        return json.load(f)


def test_normalize_then_format_round_trips_button_names():
    raw = _load()
    internal = input_remap.normalize_profile_notation(raw)
    # buttons normalized to numeric-index string keys
    assert internal["buttons"]["0"] == "space"   # a
    assert internal["buttons"]["1"] == "escape"  # b
    readable = input_remap.format_profile_notation(internal)
    assert readable["buttons"]["a"] == "space"
    assert readable["buttons"]["b"] == "escape"


def test_parse_profile_btn_key_aliases():
    assert input_remap.parse_profile_btn_key("a") == "0"
    assert input_remap.parse_profile_btn_key("start") == "7"
    assert input_remap.parse_profile_btn_key("3") == "3"


def test_parse_slot_binding_modes():
    assert input_remap.parse_slot_binding("space") == ("space", "hold")
    assert input_remap.parse_slot_binding(
        {"binding": "space", "mode": "toggle"}
    ) == ("space", "toggle")
    assert input_remap.parse_slot_binding(None) == ("none", "hold")


def test_default_chords_shape():
    ch = input_remap.default_chords()
    assert set(ch.keys()) == {"lb", "rb"}
    for mod in ("lb", "rb"):
        assert set(ch[mod].keys()) == {"0", "1", "2", "3"}
```

- [ ] **Step 2: Run to verify it passes**

Run: `pytest tests/test_profiles_golden.py -v`
Expected: PASS. If an assert mismatches current behavior, fix the assert to match the actual current output.

- [ ] **Step 3: Commit**

```bash
git add tests/test_profiles_golden.py
git commit -m "[test] Golden tests for input-profile notation"
```

### Task 1.4: Golden tests for bindings cycling

**Files:**
- Test: `tests/test_bindings_golden.py`

- [ ] **Step 1: Write the test**

```python
import input_remap


def test_cycle_binding_advances_and_wraps():
    bindings = input_remap.BUTTON_BINDINGS
    first = bindings[0][0]
    second = bindings[1][0]
    last = bindings[-1][0]
    assert input_remap.cycle_binding(first) == second
    assert input_remap.cycle_binding(last) == first


def test_binding_label_known_and_unknown():
    assert input_remap.binding_label("none") == "—"
    # unknown id falls back to the id itself
    assert input_remap.binding_label("definitely_not_a_binding") == "definitely_not_a_binding"


def test_cycle_stick_mode():
    assert input_remap.cycle_stick_mode("none") == "wasd"
    assert input_remap.cycle_stick_mode("arrows") == "none"
    assert input_remap.cycle_right_stick_mode("none") == "mouse"
    assert input_remap.cycle_right_stick_mode("mouse") == "none"
```

- [ ] **Step 2: Run; fix asserts to match current behavior if needed**

Run: `pytest tests/test_bindings_golden.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_bindings_golden.py
git commit -m "[test] Golden tests for binding cycling/labels"
```

### Task 1.5: Golden tests for game categorization

**Files:**
- Test: `tests/test_games_model_golden.py`

- [ ] **Step 1: Write the test**

```python
import launcher

GAMES = [
    {"name": "HL2", "platform": "steam"},
    {"name": "RL", "platform": "epic"},
    {"name": "Z", "platform": "nsp", "nsp_filename": "Zelda.nsp"},
    {"name": "Mystery", "platform": "weird"},
]


def test_game_sections_order_and_omission():
    sections = launcher._game_sections(GAMES)
    titles = [t for t, _ in sections]
    assert titles == ["Steam", "Epic Games", "Nintendo Switch", "Other"]
    # empty platform bucket omitted
    assert launcher._game_sections([{"name": "A", "platform": "steam"}]) == \
        [("Steam", [{"name": "A", "platform": "steam"}])]


def test_build_categorized_game_list_headers_then_games():
    items = launcher.build_categorized_game_list(
        [{"name": "A", "platform": "steam"}]
    )
    assert items[0] == {"kind": "header", "title": "Steam"}
    assert items[1]["kind"] == "game"
    assert items[1]["game"]["name"] == "A"


def test_build_tile_sections_shape():
    secs = launcher.build_tile_sections([{"name": "A", "platform": "epic"}])
    assert secs == [{"title": "Epic Games", "games": [{"name": "A", "platform": "epic"}]}]


def test_tile_selection_title_nsp_prefers_filename():
    g = {"name": "X", "platform": "nsp", "nsp_filename": "Zelda.nsp"}
    assert launcher._tile_selection_title(g) == "Zelda.nsp"
```

- [ ] **Step 2: Run; fix asserts to match current behavior if needed**

Run: `pytest tests/test_games_model_golden.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_games_model_golden.py
git commit -m "[test] Golden tests for game categorization"
```

### Task 1.6: Golden tests for tile grid + text wrapping (pure geometry)

**Files:**
- Test: `tests/test_tile_grid_golden.py`
- Test: `tests/test_fonts_golden.py`

- [ ] **Step 1: Write the tile-grid test capturing current numbers**

```python
import launcher


def test_compute_tile_grid_invariants_1080p():
    grid = launcher.compute_tile_grid(1920, 1080, hint_line_h=21, tile_scale=2.5)
    assert grid["cols"] >= 2
    assert grid["tile_w"] == grid["tile_h"]
    # grid content fits inside usable width
    usable_w = 1920 - 2 * grid["side_margin"]
    assert grid["cols"] * grid["tile_w"] + grid["gap"] * (grid["cols"] - 1) <= usable_w
    assert grid["tile_scale"] == 2.5


def test_compute_tile_grid_smaller_scale_more_cols():
    big = launcher.compute_tile_grid(1920, 1080, 21, tile_scale=4.0)
    small = launcher.compute_tile_grid(1920, 1080, 21, tile_scale=1.0)
    assert small["cols"] >= big["cols"]
```

- [ ] **Step 2: Write the text-wrap test with a fake font**

```python
import launcher


class FakeFont:
    """Monospace-ish: width = chars * 10 px."""
    def size(self, text):
        return (len(text) * 10, 12)


def test_wrap_words_to_width_breaks_on_space():
    font = FakeFont()
    lines = launcher._wrap_words_to_width(font, "aa bb cc", 50)  # 5 chars/line
    assert lines == ["aa bb", "cc"]


def test_hard_break_long_word():
    font = FakeFont()
    lines = launcher._hard_break_word(font, "abcdef", 30)  # 3 chars/line
    assert lines == ["abc", "def"]
```

- [ ] **Step 3: Run both; fix asserts to match current output if needed**

Run: `pytest tests/test_tile_grid_golden.py tests/test_fonts_golden.py -v`
Expected: PASS. These pin the exact current geometry — if a number differs, set the assert to the observed value (do not change `launcher.py`).

- [ ] **Step 4: Commit**

```bash
git add tests/test_tile_grid_golden.py tests/test_fonts_golden.py
git commit -m "[test] Golden tests for tile grid and text wrapping"
```

### Task 1.7: Create the empty `joypad` package skeleton

**Files:**
- Create: `joypad/__init__.py` and empty module files per the File Structure.

- [ ] **Step 1: Create package dirs and `__init__.py` files**

Run:
```bash
mkdir -p joypad/config joypad/games joypad/covers joypad/launch joypad/input joypad/ui/views joypad/platform
touch joypad/__init__.py joypad/config/__init__.py joypad/games/__init__.py joypad/covers/__init__.py joypad/launch/__init__.py joypad/input/__init__.py joypad/ui/__init__.py joypad/ui/views/__init__.py joypad/platform/__init__.py
```

- [ ] **Step 2: Add a version string to `joypad/__init__.py`**

```python
"""Joypad Launcher — gamepad-controlled game launcher (Windows)."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Verify the package imports**

Run: `python -c "import joypad; print(joypad.__version__)"`
Expected: prints `0.1.0`.

- [ ] **Step 4: Commit**

```bash
git add joypad/
git commit -m "[refactor] Add empty joypad package skeleton"
```

---

# Stage 2 — OS isolation layer (`joypad/platform/windows.py`)

Goal: relocate ALL Windows-specific code (ctypes/winreg/window/process-tree) from `launcher.py` and the Windows parts of `input_remap.py` into one module. Flat files re-import from it. App still runs the old way.

### Task 2.1: Move launcher.py Windows/window functions into `platform/windows.py`

**Files:**
- Create: `joypad/platform/windows.py`
- Modify: `launcher.py`

Functions to VERBATIM MOVE from `launcher.py` (current line ranges):
`_get_steam_path_from_registry` (460), `get_steam_path` (487), `_send_launcher_to_back` (666), `_get_process_and_descendant_pids` (680), `_bring_process_window_to_foreground` (732), `_bring_game_to_foreground` (762), `_bring_any_other_window_to_foreground` (778), `_bring_launcher_to_front` (810), `_yield_for_game_window` (823), `_wait_for_game_and_restore` (831), `_show_error_message` (2417).

> `get_steam_path(config)` reads `config["steam_path"]` then falls back to the registry — keep it here; it is OS-coupled. `_wait_for_game_and_restore` calls `input_remap.wait_for_game_exe_exit` lazily (line 861) — keep that lazy import as-is.

- [ ] **Step 1: Create `joypad/platform/windows.py`** with the module docstring and the moved functions

Header:
```python
"""Windows-only OS integration: registry, window focus, process trees.

The ONLY module permitted to touch ctypes / winreg / win32 APIs. Keep all
ctypes imports lazy (inside functions) so the package imports on non-Windows
dev boxes, matching the original launcher.py behavior.
"""

import os
import subprocess
import sys
import time
```
Then paste the 11 functions listed above VERBATIM (including their own inner `import ctypes` / `import winreg` lines exactly as they are today).

- [ ] **Step 2: In `launcher.py`, delete those 11 functions** and add, near the other imports inside `run_launcher`/usage sites, a top-of-call re-import. Simplest 1:1 approach: add a module-level shim block after the existing imports:

```python
from joypad.platform.windows import (
    _get_steam_path_from_registry,
    get_steam_path,
    _send_launcher_to_back,
    _get_process_and_descendant_pids,
    _bring_process_window_to_foreground,
    _bring_game_to_foreground,
    _bring_any_other_window_to_foreground,
    _bring_launcher_to_front,
    _yield_for_game_window,
    _wait_for_game_and_restore,
    _show_error_message,
)
```

> This keeps every existing call site (`_show_error_message(...)`, `get_steam_path(config)`, etc.) working with zero edits.

- [ ] **Step 3: Verify behavior-preserving move with a diff**

Run:
```bash
git show HEAD:launcher.py | grep -nE '^def (_get_steam_path_from_registry|get_steam_path|_send_launcher_to_back|_get_process_and_descendant_pids|_bring_process_window_to_foreground|_bring_game_to_foreground|_bring_any_other_window_to_foreground|_bring_launcher_to_front|_yield_for_game_window|_wait_for_game_and_restore|_show_error_message)'
```
Then confirm each function body in `joypad/platform/windows.py` matches the original (visual diff of each function). Expected: bodies identical; only the file location changed.

- [ ] **Step 4: Verify imports + tests**

Run:
```bash
python -c "import launcher, joypad.platform.windows"
pytest -q
```
Expected: clean import, all golden tests still PASS.

- [ ] **Step 5: Manual smoke (user, Windows)**

Run: `python launcher.py`
Expected: launcher opens and behaves exactly as before; launching a Steam game still restores the desktop on exit.

- [ ] **Step 6: Commit**

```bash
git add joypad/platform/windows.py launcher.py
git commit -m "[refactor] Move launcher Windows/window code into joypad.platform.windows"
```

---

# Stage 3 — Leaf domains (no pygame in the domain logic)

Goal: relocate config, games, covers, launch, and the `input/` engine modules. Flat `launcher.py` / `input_remap.py` re-import from the new homes so call sites stay unchanged.

### Task 3.1: `joypad/config/` (loader, theme, settings)

**Files:**
- Create: `joypad/config/loader.py`, `joypad/config/theme.py`, `joypad/config/settings.py`
- Modify: `launcher.py`

VERBATIM MOVE from `launcher.py`:
- → `theme.py`: the color/font default constants `BG_COLOR`, `TEXT_COLOR`, `HIGHLIGHT_COLOR`, `TITLE_COLOR` (44–47), `_parse_color` (102), `_parse_font_size` (133), `_parse_font_bold` (144), `_parse_font_scale` (159), `_parse_positive_float` (170), `_theme_from_config` (180), `_scale_theme_fonts_for_screen` (200).
- → `loader.py`: `load_config` (228), `save_config` (248). Move `CONFIG_PATH`/`CONFIG_EXAMPLE`/`_BASE_DIR` derivation too? **No** — leave `_BASE_DIR` in `launcher.py` for now (it is consumed widely); pass paths in. Have `loader.py` accept explicit paths:
  ```python
  def load_config(config_path, example_path):
      ...
  ```
  Then in `launcher.py` call `load_config(CONFIG_PATH, CONFIG_EXAMPLE)`. If the current `load_config()` reads globals, adapt the two call sites only (this is the one allowed signature change; document it in the commit). If you prefer strict 1:1, instead re-export module globals — but the explicit-path version is cleaner and the behavior is identical.
- → `settings.py`: `_cycle_option` (264), `_on_off` (273), `_background_enabled` (277), `_steam_silent_on` (300?), `_nsp_association_on` (304), `build_settings_menu` (311), `apply_setting_toggle` (366). (`resolve_background_image` (287) goes to UI in Stage 4 — leave it in launcher for now.)

- [ ] **Step 1: Create `theme.py`** with the constants and the 8 functions VERBATIM. Top imports: none beyond stdlib (no pygame).

- [ ] **Step 2: Create `loader.py`** with `load_config`/`save_config` (adapted to explicit path args as noted) and `import json, os`.

- [ ] **Step 3: Create `settings.py`** with the settings-menu functions VERBATIM. It imports theme helpers if needed: `from joypad.config.theme import _on_off`? (Check actual internal calls and wire imports accordingly.)

- [ ] **Step 4: In `launcher.py`** delete the moved defs/constants and add re-import shims:

```python
from joypad.config.theme import (
    BG_COLOR, TEXT_COLOR, HIGHLIGHT_COLOR, TITLE_COLOR,
    _parse_color, _parse_font_size, _parse_font_bold, _parse_font_scale,
    _parse_positive_float, _theme_from_config, _scale_theme_fonts_for_screen,
)
from joypad.config.loader import load_config, save_config
from joypad.config.settings import (
    _cycle_option, _on_off, _background_enabled, _steam_silent_on,
    _nsp_association_on, build_settings_menu, apply_setting_toggle,
)
```
Update the two `load_config(...)` call sites to pass `CONFIG_PATH, CONFIG_EXAMPLE`.

- [ ] **Step 5: Point the golden theme test at the new module too**

Add to `tests/test_theme_golden.py`:
```python
from joypad.config import theme as joypad_theme


def test_theme_module_matches_launcher_reexport():
    assert joypad_theme._parse_color("#fff", (0, 0, 0)) == (255, 255, 255)
    assert joypad_theme._theme_from_config({"theme": {}})["text"] == joypad_theme.TEXT_COLOR
```

- [ ] **Step 6: Verify**

Run:
```bash
python -c "import launcher, joypad.config.loader, joypad.config.theme, joypad.config.settings"
pytest -q
```
Expected: clean import; all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add joypad/config launcher.py tests/test_theme_golden.py
git commit -m "[refactor] Extract config loader/theme/settings into joypad.config"
```

### Task 3.2: `joypad/games/` (model, scan, scan_debug)

**Files:**
- Create: `joypad/games/model.py`, `joypad/games/scan.py`, `joypad/games/scan_debug.py`
- Modify: `launcher.py`; Delete: `scan_libraries.py`, `scan_debug.py`

VERBATIM MOVE:
- → `model.py` from `launcher.py`: `_game_sections` (924), `build_categorized_game_list` (957), `build_tile_sections` (967), `_ui_mode_from_theme` (972), `_ui_mode_label` (979), `_tile_selection_title` (983).
- → `scan.py`: entire `scan_libraries.py` content (the `scan_all`, `scan_nsp_games`, and helpers). It imports `vdf` and uses Windows registry via ctypes/winreg — if so, route those OS calls through `joypad.platform.windows` where a function already exists; otherwise keep its own ctypes lazy imports (it has 10 OS hits). For 1:1, keep its internal logic; only move the registry-path helper to `platform/windows.py` if it duplicates `_get_steam_path_from_registry` (reuse, don't duplicate).
- → `scan_debug.py`: entire `scan_debug.py` content.

- [ ] **Step 1: Create `joypad/games/scan.py`** = `scan_libraries.py` VERBATIM (update any internal `from X import` to new homes). Keep `import vdf`.

- [ ] **Step 2: Create `joypad/games/scan_debug.py`** = `scan_debug.py` VERBATIM; fix its imports to `from joypad.games.scan import ...`.

- [ ] **Step 3: Create `joypad/games/model.py`** with the 6 functions VERBATIM (`import os` for `_tile_selection_title`).

- [ ] **Step 4: Update `launcher.py`** — replace `from scan_libraries import scan_all` (line ~1060) and `from scan_libraries import scan_nsp_games` (~1070) with `from joypad.games.scan import scan_all, scan_nsp_games`; delete the 6 model functions and add:
```python
from joypad.games.model import (
    _game_sections, build_categorized_game_list, build_tile_sections,
    _ui_mode_from_theme, _ui_mode_label, _tile_selection_title,
)
```

- [ ] **Step 5: Repoint golden test**

Edit `tests/test_games_model_golden.py` top: change `import launcher` to `from joypad.games import model as launcher` (the test references `launcher._game_sections` etc.; the alias keeps the body unchanged). Run it to confirm parity.

- [ ] **Step 6: Delete the now-relocated flat files**

Run: `git rm scan_libraries.py scan_debug.py`

- [ ] **Step 7: Verify**

Run:
```bash
grep -rn "import scan_libraries\|import scan_debug\|from scan_libraries\|from scan_debug" . --include=*.py
python -c "import launcher, joypad.games.scan, joypad.games.model, joypad.games.scan_debug"
pytest -q
```
Expected: first grep returns nothing; imports clean; tests PASS.

- [ ] **Step 8: Commit**

```bash
git add joypad/games launcher.py tests/test_games_model_golden.py
git commit -m "[refactor] Extract game model + scanners into joypad.games"
```

### Task 3.3: `joypad/covers/` (cache, cdn)

**Files:**
- Create: `joypad/covers/cache.py`, `joypad/covers/cdn.py`
- Modify: `launcher.py`, `covers.py` consumers; Delete: `covers.py`, `cover_cdn.py`

- [ ] **Step 1: Create `joypad/covers/cdn.py`** = `cover_cdn.py` VERBATIM.

- [ ] **Step 2: Create `joypad/covers/cache.py`** = `covers.py` VERBATIM, changing its import `from cover_cdn import CdnCoverStore, nsp_cover_stems` → `from joypad.covers.cdn import CdnCoverStore, nsp_cover_stems`. (This module loads images via pygame — keep its pygame import as-is.)

- [ ] **Step 3: Update `launcher.py`** — replace `from covers import CoverCache` (line ~1093) with `from joypad.covers.cache import CoverCache`.

- [ ] **Step 4: Delete flat files**

Run: `git rm covers.py cover_cdn.py`

- [ ] **Step 5: Verify**

Run:
```bash
grep -rn "from covers import\|import covers\b\|from cover_cdn import\|import cover_cdn" . --include=*.py
python -c "import launcher"
pytest -q
```
Expected: grep empty; import clean (note: importing `launcher` triggers pygame — fine on dev box with pygame installed); tests PASS.

- [ ] **Step 6: Commit**

```bash
git add joypad/covers launcher.py
git commit -m "[refactor] Move cover cache + CDN into joypad.covers"
```

### Task 3.4: `joypad/launch/launcher.py` (game launching + system actions)

**Files:**
- Create: `joypad/launch/launcher.py`
- Modify: `launcher.py`

VERBATIM MOVE from `launcher.py`:
`launch_steam_game` (512), `launch_epic_game` (526), `_ShellExecuteProcess` (538), `_shell_execute_open_file` (572), `launch_nsp_game` (622), `perform_system_action` (647), `_try_launch_game` (878).

> `_try_launch_game` calls `get_steam_path`-derived `steam_path` (passed in as arg) and `_send_launcher_to_back`/foreground helpers — those now live in `joypad.platform.windows`. Add `from joypad.platform.windows import _send_launcher_to_back` etc. inside `joypad/launch/launcher.py` as needed (check its body). Keep the lazy `subprocess`/ctypes imports as they are.

- [ ] **Step 1: Create `joypad/launch/launcher.py`** with `import os, subprocess, sys, time` and the 7 items VERBATIM; wire any window-helper calls to `from joypad.platform.windows import ...`.

- [ ] **Step 2: Update `launcher.py`** — delete those defs and add:
```python
from joypad.launch.launcher import (
    launch_steam_game, launch_epic_game, launch_nsp_game,
    perform_system_action, _try_launch_game,
)
```

- [ ] **Step 3: Diff check** the moved bodies against `git show HEAD:launcher.py` for those functions (only import/reference lines may differ).

- [ ] **Step 4: Verify**

Run:
```bash
python -c "import launcher, joypad.launch.launcher"
pytest -q
```
Expected: clean; tests PASS.

- [ ] **Step 5: Manual smoke (user, Windows):** launch one Steam, one Epic, and (if configured) one NSP game; confirm identical behavior.

- [ ] **Step 6: Commit**

```bash
git add joypad/launch launcher.py
git commit -m "[refactor] Move game launching + system actions into joypad.launch"
```

### Task 3.5: `joypad/input/` — log, profiles, bindings (pure parts first)

**Files:**
- Create: `joypad/input/log.py`, `joypad/input/profiles.py`, `joypad/input/bindings.py`
- Modify: `input_remap.py`

VERBATIM MOVE from `input_remap.py`:
- → `log.py`: `remap_log_enabled` (553), `remap_log_path` (557), `init_remap_log` (561), `remap_log` (576), plus module globals `REMAP_LOG_NAME` (16), `_remap_log_path` (20).
- → `bindings.py`: `_build_keyboard_bindings` (241) + the module-level `VK, _KEYBOARD_BINDINGS = _build_keyboard_bindings()` (273), `BUTTON_BINDINGS` (275), `DPAD_BINDINGS` (284), `XINPUT_DPAD` (291), `XINPUT_FACE` (298), `binding_label` (468), `cycle_binding` (475), `cycle_stick_mode` (484), `cycle_right_stick_mode` (491), and the constants they need: `STICK_MODES`, `RIGHT_STICK_MODES` (32–33), `BTN_*` indices (23–30), `BTN_FACE` (36).
- → `profiles.py`: all notation parse/format (62–238), `game_remap_key` (314), `remap_settings` (327), `profiles_dir` (331), `profile_file_path` (338), `get_assigned_profile_id` (343), `resolve_profile_path` (355), `default_chords` (363), `ensure_chords` (370), `parse_chord_slot_key` (379), `default_profile_path` (389), `_load_profile_raw` (393), `merge_profiles` (401), `load_default_profile` (414), `prepare_profile` (426), `default_profile` (440), `load_profile` (447), `save_profile` (460), `list_remapped_games` (495), `assign_game_profile` (511), `unassign_game` (527), `suggest_profile_id` (547), and the constants `PROFILES_DIR_DEFAULT` (13), `DEFAULT_PROFILE_ID` (14), `SLOT_BINDING_MODES` (34), `BTN_PROFILE_NAMES`/`FACE_PROFILE_NAMES`/aliases (39–59).

> Shared constants (`BTN_*`, `BTN_PROFILE_NAMES`, etc.) are needed by both `bindings.py` and `profiles.py` and later `engine.py`. To avoid duplication, put the shared gamepad constants in a small `joypad/input/constants.py` and import from there. (Add this file to the package — it is a natural unit, not scope creep.)

- [ ] **Step 1: Create `joypad/input/constants.py`** with the shared constants (`BTN_*`, `BTN_FACE`, `STICK_MODES`, `RIGHT_STICK_MODES`, `SLOT_BINDING_MODES`, `BTN_PROFILE_NAMES`, `FACE_PROFILE_NAMES`, `_BTN_PROFILE_ALIASES`, `_FACE_PROFILE_ALIASES`, `PROFILES_DIR_DEFAULT`, `DEFAULT_PROFILE_ID`, `TRIGGER_THRESHOLD`, `GAME_WATCH_GRACE`, `GAME_WATCH_ACTIVITY_GRACE`) VERBATIM from `input_remap.py` top.

- [ ] **Step 2: Create `log.py`, `bindings.py`, `profiles.py`** with the functions VERBATIM, importing shared names `from joypad.input.constants import ...` and `import copy, json, os` as needed.

- [ ] **Step 3: Update `input_remap.py`** — delete the moved code and re-import:
```python
from joypad.input.constants import *  # noqa: F401,F403  (shared gamepad constants)
from joypad.input.log import remap_log, remap_log_enabled, remap_log_path, init_remap_log
from joypad.input.bindings import (
    VK, BUTTON_BINDINGS, DPAD_BINDINGS, XINPUT_DPAD, XINPUT_FACE,
    binding_label, cycle_binding, cycle_stick_mode, cycle_right_stick_mode,
    _build_keyboard_bindings,
)
from joypad.input.profiles import (
    parse_profile_btn_key, parse_profile_face_key, parse_slot_binding,
    format_slot_binding, normalize_profile_notation, format_profile_notation,
    game_remap_key, remap_settings, resolve_profile_path, default_chords,
    ensure_chords, merge_profiles, load_profile, save_profile, prepare_profile,
    default_profile, list_remapped_games, assign_game_profile, unassign_game,
    suggest_profile_id, get_assigned_profile_id, profiles_dir,
    profile_file_path, default_profile_path, parse_chord_slot_key,
    load_default_profile,
)
```
(Keep the engine/watch/worker code in `input_remap.py` for now — Stage 3.6.)

- [ ] **Step 4: Repoint the two golden tests** that used `import input_remap`: they still work through the re-export, but add a direct-module assertion:
```python
# tests/test_profiles_golden.py
from joypad.input import profiles as jp_profiles
def test_profiles_module_direct():
    assert jp_profiles.parse_profile_btn_key("start") == "7"
```

- [ ] **Step 5: Verify**

Run:
```bash
python -c "import input_remap, joypad.input.profiles, joypad.input.bindings, joypad.input.log, joypad.input.constants"
pytest -q
```
Expected: clean; tests PASS.

- [ ] **Step 6: Commit**

```bash
git add joypad/input launcher.py input_remap.py tests/test_profiles_golden.py
git commit -m "[refactor] Extract input profiles/bindings/log/constants into joypad.input"
```

### Task 3.6: `joypad/input/` — engine, watch, worker (OS-coupled parts)

**Files:**
- Create: `joypad/input/engine.py`, `joypad/input/watch.py`, `joypad/input/worker.py`
- Modify: `input_remap.py` (until it becomes empty/removed in Stage 6)

VERBATIM MOVE from `input_remap.py`:
- → `engine.py`: the XInput/SendInput layer and `run_remap_loop` — `_key_event_vk` (668) through `_apply_deadzone` (788), `_scan_xinput_indices` (1394), `_pick_xinput_index` (1405), `run_remap_loop` (1415) **and** its non-Windows fallback `run_remap_loop` (1550). Keep the `if sys.platform == "win32":` guard structure EXACTLY as today so the right definition wins at import time.
- → `watch.py`: `_get_process_tree_pids` (794), `_any_pid_alive` (844), `_enum_process_ids` (1152), `_process_image_path` (1190), `_find_pids_in_directory` (1204), `_find_pids_by_exe_stem` (1221), `_find_pids_by_exe_name` (1268), `_find_pids_by_window_substring` (1275), `_gamepad_active` (1305), `_active_game_pids` (1317), `_alive_pids` (1333), `game_process_alive` (1353 + fallback 1556), `wait_for_game_exe_exit` (1357 + fallback 1553), `game_watch_targets` (537). Reuse `joypad.platform.windows._get_process_and_descendant_pids` where `watch.py` duplicates process-tree enumeration — if logic is identical, import it; if subtly different, keep watch's own copy (note which in the commit body) to preserve behavior 1:1.
- → `worker.py`: `start_remap_worker` (1560), `stop_remap_worker` (1612), `run_remap_worker_main` (1641 → end).

> Preserve the dual `if sys.platform`-guarded definitions verbatim. `worker.py` builds the spawn command `[sys.executable, os.path.join(base_dir, "launcher.py"), "--input-remap-worker", ...]` — leave this string `"launcher.py"` unchanged; the shim (Stage 6) routes it. In frozen mode it uses `[sys.executable] + worker_args` — also unchanged.

- [ ] **Step 1: Create `engine.py`, `watch.py`, `worker.py`** with the functions VERBATIM. Imports: `import ctypes, math, os, subprocess, sys, time` as each needs; `from joypad.input.constants import ...`; `from joypad.input.log import remap_log, init_remap_log`; `engine.py` imports profile loaders from `joypad.input.profiles`; `worker.py` imports `run_remap_loop` from `joypad.input.engine` and watch helpers from `joypad.input.watch`.

- [ ] **Step 2: Update `input_remap.py`** — delete the moved code, re-export for any remaining external callers:
```python
from joypad.input.engine import run_remap_loop
from joypad.input.watch import (
    game_process_alive, wait_for_game_exe_exit, game_watch_targets,
)
from joypad.input.worker import (
    start_remap_worker, stop_remap_worker, run_remap_worker_main,
)
```

- [ ] **Step 3: Add a worker-entry parity test** (no Windows needed — just that argparse parsing path is reachable):

`tests/test_entry_dispatch.py`:
```python
import joypad.input.worker as worker


def test_run_remap_worker_main_requires_profile():
    # argparse should exit(2) when --profile missing
    import pytest
    with pytest.raises(SystemExit):
        worker.run_remap_worker_main(["--pid", "1234"])
```

- [ ] **Step 4: Verify**

Run:
```bash
python -c "import input_remap, joypad.input.engine, joypad.input.watch, joypad.input.worker"
pytest -q
```
Expected: clean; tests PASS. (On Linux dev box, the non-Windows fallback definitions are exercised — that is the intended 1:1 behavior.)

- [ ] **Step 5: Manual smoke (user, Windows):** assign a remap profile to a game, launch it, confirm the worker spawns and remapping works, and that it stops on game exit (check `input_remap.log` if logging on).

- [ ] **Step 6: Commit**

```bash
git add joypad/input input_remap.py tests/test_entry_dispatch.py
git commit -m "[refactor] Extract remap engine/watch/worker into joypad.input"
```

---

# Stage 4 — UI layer

Goal: relocate pygame helpers, the two views, overlays, background, and the editor. The big `run_launcher` loop still lives in `launcher.py` and calls these — Stage 5 slims it.

### Task 4.1: `joypad/ui/fonts.py` and `joypad/ui/background.py`

**Files:**
- Create: `joypad/ui/fonts.py`, `joypad/ui/background.py`
- Modify: `launcher.py`

VERBATIM MOVE from `launcher.py`:
- → `fonts.py`: `_hard_break_word` (50), `_wrap_words_to_width` (69). (Pure — no pygame import needed at module level; they receive a `font` object.)
- → `background.py`: `_background_enabled` (277) [if not already moved to settings — if it was moved in 3.1, import it from there instead], `resolve_background_image` (287), `_load_background_surface` (447, uses pygame). `background.py` imports pygame lazily inside `_load_background_surface` exactly as today.

- [ ] **Step 1: Create `fonts.py`** with the two functions VERBATIM.

- [ ] **Step 2: Create `background.py`** with `resolve_background_image` and `_load_background_surface` VERBATIM; if `_background_enabled` already lives in `joypad.config.settings`, do `from joypad.config.settings import _background_enabled` and re-export.

- [ ] **Step 3: Update `launcher.py`** — delete moved defs, add:
```python
from joypad.ui.fonts import _hard_break_word, _wrap_words_to_width
from joypad.ui.background import resolve_background_image, _load_background_surface
```

- [ ] **Step 4: Repoint** `tests/test_fonts_golden.py`: add `from joypad.ui import fonts` and a direct assertion mirroring one existing test.

- [ ] **Step 5: Verify**

Run: `python -c "import launcher, joypad.ui.fonts, joypad.ui.background"` then `pytest -q`
Expected: clean; tests PASS.

- [ ] **Step 6: Commit**

```bash
git add joypad/ui/fonts.py joypad/ui/background.py launcher.py tests/test_fonts_golden.py
git commit -m "[refactor] Move font wrapping + background loading into joypad.ui"
```

### Task 4.2: `joypad/ui/editor.py` (input remap editor)

**Files:**
- Create: `joypad/ui/editor.py`
- Modify: `launcher.py`; Delete: `input_remap_editor.py`

- [ ] **Step 1: Create `joypad/ui/editor.py`** = `input_remap_editor.py` VERBATIM, changing its import `from input_remap import (...)` (line 10) to pull from the new homes: `from joypad.input.profiles import ...`, `from joypad.input.bindings import ...` as appropriate (split the existing import list across the two modules based on where each name now lives).

- [ ] **Step 2: Update `launcher.py`** — the two lazy imports `from input_remap_editor import InputRemapSession` (lines ~1856, ~1885) become `from joypad.ui.editor import InputRemapSession`.

- [ ] **Step 3: Delete the flat file**

Run: `git rm input_remap_editor.py`

- [ ] **Step 4: Verify**

Run:
```bash
grep -rn "input_remap_editor" . --include=*.py
python -c "import launcher, joypad.ui.editor"
pytest -q
```
Expected: grep empty; clean import; tests PASS.

- [ ] **Step 5: Manual smoke (user, Windows):** open the in-app remap editor, change a binding, save, confirm it persists to the profile JSON identically.

- [ ] **Step 6: Commit**

```bash
git add joypad/ui/editor.py launcher.py
git commit -m "[refactor] Move input remap editor into joypad.ui.editor"
```

---

# Stage 5 — Core: AppState + slim app.py

Goal: introduce `AppState`, move the nested view/overlay functions out of `run_launcher` into `joypad/ui/`, and reduce `run_launcher` to an orchestration loop in `joypad/app.py`. This is the highest-risk stage — go in the smallest increments and smoke-test each.

### Task 5.1: Define `AppState`

**Files:**
- Create: `joypad/app_state.py`

- [ ] **Step 1: Inventory the closure variables.** Read `run_launcher` (launcher.py 1055–2416) and list every local variable that is read or assigned across more than one nested function (selection index, scroll offsets, fonts dict, theme, screen, clock, games/sections, ui_mode, tile geometry dict, overlay state/flags, active remap process handle, etc.).

- [ ] **Step 2: Create `joypad/app_state.py`** as a dataclass capturing exactly those fields, each with the SAME name and the SAME initial value the closure uses today. Example shape (fill in from the actual inventory — do not invent fields):

```python
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AppState:
    config: dict
    theme: dict
    screen: Any = None
    clock: Any = None
    games: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    selection: int = 0
    scroll_y: int = 0
    ui_mode: str = "list"
    fonts: dict = field(default_factory=dict)
    tile_geometry: Optional[dict] = None
    overlay_active: bool = False
    overlay_kind: Optional[str] = None
    overlay_selection: int = 0
    active_remap_proc: Any = None
    # ... every other shared closure variable, named identically
```

- [ ] **Step 3: Verify it imports**

Run: `python -c "from joypad.app_state import AppState; AppState(config={}, theme={})"`
Expected: no error.

- [ ] **Step 4: Commit**

```bash
git add joypad/app_state.py
git commit -m "[refactor] Add AppState dataclass for the launcher game loop"
```

### Task 5.2: Introduce `state` inside `run_launcher` (still in launcher.py)

**Files:**
- Modify: `launcher.py`

This MUST happen before any view function is extracted: the extracted functions take `state` as their first argument, so `state` has to exist at their call sites first. The loop stays in `launcher.py` for now.

- [ ] **Step 1: At the top of `run_launcher`**, after the existing locals are initialized, construct `state = AppState(config=config, theme=theme, ...)` populating every field from the matching local.

- [ ] **Step 2: Replace closure locals with `state.<field>` incrementally**, in small batches (e.g. selection/scroll first, then fonts/theme, then tile geometry, then overlay flags). After each batch run a smoke check. Where a local is reassigned (`selection = ...`), change to `state.selection = ...`. Do NOT change any logic.

- [ ] **Step 3: Verify**

Run: `python -c "import launcher"` then `pytest -q`
Expected: clean; tests PASS.

- [ ] **Step 4: Manual smoke (user, Windows):** full navigation in both views still identical.

- [ ] **Step 5: Commit**

```bash
git add launcher.py
git commit -m "[refactor] Route run_launcher closure state through AppState"
```

### Task 5.3: Move tile view functions to `joypad/ui/views/tiles.py`

**Files:**
- Create: `joypad/ui/views/tiles.py`
- Modify: `launcher.py`

Move these (currently nested in `run_launcher`) plus the module-level `compute_tile_grid` (996) and `_parse_tile_scale` (1043): `rebuild_tile_geometry`, `tile_row_stride`, `rebuild_tile_layout`, `tile_selected_game`, `_tile_pick_location`, `_global_pick`, `_tile_entry_for_pick`, `_section_header_y_for_pick`, `tile_max_scroll_y`, `_tile_snap_scroll`, `_tile_step_section`, `_tile_below`, `_tile_above`, `tile_move`, `tile_page_scroll`, `tile_section_jump`, `draw_tiles_view`, `_truncate_to_width`.

Conversion rule: each nested function becomes a module function whose first parameter is `state: AppState`. Replace each free variable that referred to a closure local with `state.<name>`. Do NOT change any arithmetic or branching.

- [ ] **Step 1: Move `compute_tile_grid` + `_parse_tile_scale` VERBATIM** to `tiles.py` (module-level, no state needed). Update `launcher.py` and `tests/test_tile_grid_golden.py` import (`from joypad.ui.views import tiles` with alias `launcher = tiles` in the test).

- [ ] **Step 2: Move ONE function first — `tile_selected_game`** — as `def tile_selected_game(state):` using `state.*`. In `run_launcher`, replace the nested def with a thin wrapper `def tile_selected_game(): return tiles.tile_selected_game(state)` so all existing call sites keep working. (`state` already exists from Task 5.2.)

- [ ] **Step 3: Move the remaining tile functions** the same way, in small batches (geometry → navigation → draw), running a smoke check after each batch.

- [ ] **Step 4: Verify**

Run: `python -c "import launcher, joypad.ui.views.tiles"` then `pytest -q`
Expected: clean; tests PASS.

- [ ] **Step 5: Manual smoke (user, Windows):** switch to Tiles view; navigate with stick/d-pad, page scroll, LB/RB section jump; confirm pixel-identical layout and selection behavior.

- [ ] **Step 6: Commit**

```bash
git add joypad/ui/views/tiles.py launcher.py tests/test_tile_grid_golden.py
git commit -m "[refactor] Move tile view into joypad.ui.views.tiles (state-driven)"
```

### Task 5.4: Move list view functions to `joypad/ui/views/list.py`

**Files:**
- Create: `joypad/ui/views/list.py`
- Modify: `launcher.py`

Move (nested in `run_launcher`): `build_list_layout`, `move_selection_by_viewport`, `page_scroll`, `_first_game_row_index`, `move_game_selection`, `_hint_surfaces`, `get_selected_item`, `nav_vertical`, `nav_horizontal`, `nav_page`, `nav_lb_rb`. Same `state`-parameter conversion rule.

> `get_selected_item`, `nav_*` dispatch between list and tile modes — keep their mode checks (`if state.ui_mode == "tiles": ...`) calling into `joypad.ui.views.tiles`.

- [ ] **Step 1: Move the functions** in small batches with the `state` first-parameter rule and thin wrappers in `run_launcher` if needed.

- [ ] **Step 2: Verify**

Run: `python -c "import launcher, joypad.ui.views.list"` then `pytest -q`
Expected: clean; tests PASS.

- [ ] **Step 3: Manual smoke (user, Windows):** List view navigation, paging, LB/RB — identical behavior.

- [ ] **Step 4: Commit**

```bash
git add joypad/ui/views/list.py launcher.py
git commit -m "[refactor] Move list view into joypad.ui.views.list (state-driven)"
```

### Task 5.5: Move overlay/settings functions to `joypad/ui/overlay.py`

**Files:**
- Create: `joypad/ui/overlay.py`
- Modify: `launcher.py`

Move (nested in `run_launcher`): `_settings_first_row`, `rebuild_settings_layout`, `overlay_items`, `_overlay_snap_scroll`, `overlay_move`, `reload_fonts_and_layout`, `apply_setting_live`, `overlay_back`, `overlay_confirm`, `show_launching_overlay`. Same conversion rule.

> `apply_setting_live` / `reload_fonts_and_layout` mutate fonts/theme on `state` and rebuild layouts — ensure they call back into `tiles`/`list` rebuild functions with `state`.

- [ ] **Step 1: Move the functions** with `state` parameter + wrappers as needed.

- [ ] **Step 2: Verify**

Run: `python -c "import launcher, joypad.ui.overlay"` then `pytest -q`
Expected: clean; tests PASS.

- [ ] **Step 3: Manual smoke (user, Windows):** open system menu (B/Back), open Settings, toggle View list/tiles, toggle CDN covers, change tile scale — all live-apply identically; "Launching…" overlay shows on launch.

- [ ] **Step 4: Commit**

```bash
git add joypad/ui/overlay.py launcher.py
git commit -m "[refactor] Move settings/system overlays into joypad.ui.overlay (state-driven)"
```

### Task 5.6: Move the loop into `joypad/app.py` with dual-mode `main`

**Files:**
- Create: `joypad/app.py`
- Modify: `launcher.py`

- [ ] **Step 1: Create `joypad/app.py`** with `run()` = the (now slim) former `run_launcher` body, building `state = AppState(...)` at the top and calling the relocated view/overlay/launch functions with `state`. Move the remaining nested helpers (`rescan_joysticks`, `stop_active_remap`, `try_launch_game`, etc.) here as inner functions or module functions taking `state`. Keep `_BASE_DIR` computation here (or in a tiny `joypad/paths.py` — your call; if you add `paths.py`, note it).

- [ ] **Step 2: Add `main(argv)`** with the dual-mode dispatch and the existing error-logging wrapper:

```python
import os
import sys


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    if len(argv) >= 2 and argv[1] == "--input-remap-worker":
        from joypad.input.worker import run_remap_worker_main
        run_remap_worker_main(argv[1:])
        return 0
    try:
        run()
        return 0
    except BaseException:
        import traceback
        from joypad.platform.windows import _show_error_message
        log_path = os.path.join(_base_dir(), "launcher_error.log")
        err_text = traceback.format_exc()
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err_text)
        except Exception:
            pass
        traceback.print_exc()
        _show_error_message("Launch error.\nDetails written to:\n%s" % log_path)
        return 1
```

> Match the CURRENT `__main__` block in `launcher.py` (lines 2427–2446) exactly: same log filename, same message text, same `sys.exit(0/1)` semantics. `run_remap_worker_main` already strips a leading `--input-remap-worker` arg (input_remap.py:1646), so passing `argv[1:]` is correct.

- [ ] **Step 3: Verify the loop still runs from app.py**

Run: `python -c "import joypad.app"` then `pytest -q`
Expected: clean; tests PASS.

- [ ] **Step 4: Manual smoke (user, Windows):** `python -m joypad.app`? No — entry stays `launcher.py` (Stage 6). For now, temporarily test via `python -c "from joypad.app import main; main(['x','--input-remap-worker','--help'])"` to confirm the worker branch dispatches (argparse prints help / exits).

- [ ] **Step 5: Commit**

```bash
git add joypad/app.py launcher.py
git commit -m "[refactor] Move game loop into joypad.app with dual-mode main()"
```

---

# Stage 6 — Finalize: thin shim, deletions, cleanup, packaging

### Task 6.1: Turn `launcher.py` into the thin shim

**Files:**
- Modify: `launcher.py`; Delete: `input_remap.py`

- [ ] **Step 1: Replace `launcher.py` entirely** with:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Joypad Launcher entry point. Real code lives in the `joypad` package."""

import sys

from joypad.app import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 2: Confirm no remaining imports of `input_remap`** (all moved to `joypad.input.*`):

Run: `grep -rn "import input_remap\|from input_remap" . --include=*.py`
Expected: empty (worker spawn uses the string `"launcher.py"`, not an import — that is fine).

- [ ] **Step 3: Delete `input_remap.py`**

Run: `git rm input_remap.py`

- [ ] **Step 4: Verify full wiring**

Run:
```bash
python -c "import launcher"
python -c "from joypad.app import main; main(['launcher.py','--input-remap-worker','--help'])" ; echo "exit=$?"
pytest -q
```
Expected: clean imports; worker `--help` path reached; all tests PASS.

- [ ] **Step 5: Manual full smoke (user, Windows):** cold-start `python launcher.py`; verify auto-scan, list AND tiles views, covers loading, launching each platform with desktop restore, remap worker spawn/stop, settings toggles, and the error dialog path (temporarily raise to confirm `launcher_error.log` is written).

- [ ] **Step 6: Commit**

```bash
git add launcher.py
git commit -m "[refactor] Reduce launcher.py to a thin entry shim; remove input_remap.py"
```

### Task 6.2: Clean up lazy imports inside the package

**Files:**
- Modify: modules across `joypad/` where intra-package functions are still imported lazily inside functions (e.g. former `from input_remap import ...` inside `run_launcher`).

- [ ] **Step 1: Find leftover function-local imports of relocated names**

Run: `grep -rn "    from joypad\.\|    import joypad" joypad/ launcher.py`
Review each: keep lazy imports that exist to defer pygame/ctypes/Windows loading (intentional); hoist purely-Python intra-package imports to module top where it doesn't introduce a cycle.

- [ ] **Step 2: Verify no import cycles**

Run: `python -c "import joypad.app"` and `pytest -q`
Expected: clean; tests PASS.

- [ ] **Step 3: Commit**

```bash
git add joypad/
git commit -m "[refactor] Tidy intra-package imports"
```

### Task 6.3: Update packaging — `build_exe.bat`

**Files:**
- Modify: `build_exe.bat`

- [ ] **Step 1: Replace the PyInstaller invocation** so it collects the package instead of naming each flat module:

```bat
py -3 -m PyInstaller --onefile --windowed --name JoypadLauncher ^
  --collect-submodules joypad --collect-submodules ddcci ^
  --add-data "config.example.json;." ^
  --add-data "input_profiles;input_profiles" ^
  --add-data "assets;assets" ^
  --clean launcher.py
```

(Remove all the `--hidden-import scan_libraries/covers/cover_cdn/input_remap/input_remap_editor` flags; `--collect-submodules joypad` covers them.)

- [ ] **Step 2: Build verification (user, Windows)**

Run: `build_exe.bat`
Expected: `dist\JoypadLauncher.exe` produced; running it launches the UI; assigning a remap profile spawns the worker (frozen mode uses `[sys.executable] + worker_args` — confirm remap works in the exe).

- [ ] **Step 3: Commit**

```bash
git add build_exe.bat
git commit -m "[build] Collect joypad package submodules in PyInstaller spec"
```

### Task 6.4: Update CI — `.github/workflows/release.yml`

**Files:**
- Modify: `.github/workflows/release.yml`

- [ ] **Step 1: Add a test gate before build.** Insert after "Install dependencies":

```yaml
      - name: Run tests
        run: |
          pip install -r requirements-dev.txt
          pytest -q
```

- [ ] **Step 2: Update the Build EXE step** to use the package collection (mirror build_exe.bat):

```yaml
      - name: Build EXE
        run: |
          python -m PyInstaller --onefile --windowed --name JoypadLauncher --collect-submodules joypad --collect-submodules ddcci --add-data "config.example.json;." --add-data "input_profiles;input_profiles" --add-data "assets;assets" --clean launcher.py
```

> Note: the current workflow only ships `config.example.json` + `bg.jpg`; this also bundles `input_profiles` and `assets` so remap + cover placeholders work from the exe. Keep the existing ZIP packaging step; add `input_profiles` to the data shipped if releasing remap defaults is desired (optional — confirm with maintainer).

- [ ] **Step 3: Verify YAML is valid**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/release.yml'))" 2>/dev/null || echo "install pyyaml to validate locally"`
Expected: no error (or skip if pyyaml absent — CI will validate on push).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "[ci] Add pytest gate and collect joypad submodules in release build"
```

### Task 6.5: Update docs

**Files:**
- Modify: `README.md` (developer/run section if it references flat modules)

- [ ] **Step 1: Update any developer-facing references** in `README.md` that mention the old flat layout (e.g. "run `python launcher.py`" stays correct; add a one-line "Project layout" note pointing at `joypad/`). Do NOT change user-facing config docs.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "[docs] Note the joypad package layout"
```

---

## Final verification checklist

- [ ] `grep -rn "from input_remap\|import input_remap\|from covers\|from cover_cdn\|from scan_libraries\|import scan_libraries\|input_remap_editor" . --include=*.py` returns nothing.
- [ ] `pytest -q` green.
- [ ] `python -c "import launcher"` and `python -c "import joypad.app"` clean.
- [ ] No file in `joypad/` other than `platform/windows.py` (and lazy fallbacks already present) calls `ctypes`/`winreg` directly: `grep -rn "ctypes\|winreg\|windll" joypad/ | grep -v "platform/windows.py"` — review remaining hits (engine.py XInput/SendInput and watch.py process enumeration are expected OS-coupled members of `joypad.input`; the spec scopes the isolation layer to *window/registry/process* code from launcher.py, with input device I/O living in `joypad.input`). Confirm nothing from launcher.py's window/registry set leaked outside `platform/windows.py`.
- [ ] Manual Windows smoke of the full app passed (list, tiles, covers, all 3 launch paths + restore, remap worker, settings, error dialog).
- [ ] `build_exe.bat` produces a working exe including remap in frozen mode.

---

## Notes on 1:1 preservation

- Every "VERBATIM MOVE" task carries a diff check; reviewers should confirm only import/reference lines changed.
- The two intentional, documented signature changes are: `load_config(config_path, example_path)` (was global-reading) and constructing `AppState` instead of closure locals. Both are behavior-preserving.
- Dual `if sys.platform`-guarded definitions in the input engine/watch are preserved exactly so non-Windows fallback behavior is unchanged.
- `joypad/input/constants.py` and the optional `joypad/paths.py` are the only NEW modules beyond the spec's named files — both are pure extraction-of-shared-constants with no logic, added to avoid duplication (DRY), consistent with the spec's intent.
