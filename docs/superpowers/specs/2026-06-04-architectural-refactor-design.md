# Architectural Refactor — Joypad Launcher

**Date:** 2026-06-04
**Status:** Approved design, pending implementation plan
**Type:** Pure structural refactor (behavior preserved 1:1, no new features)

## Motivation

The project grew organically from a single script into ~7000 lines across flat
top-level files. Three files dominate:

- `launcher.py` — 2446 lines, with a single `run_launcher()` function of ~1360
  lines mixing config, theme parsing, game launching, Windows window/process
  management, pygame rendering, navigation, the settings menu, and tile layout.
- `input_remap.py` — 1667 lines: remap engine + worker subprocess + keyboard
  bindings + profile management.
- `input_remap_editor.py` — 1110 lines: the remap editor UI.

The refactor serves four goals the user confirmed, all at once:

1. **Easier to add features** — clear modules with well-defined boundaries.
2. **Testability** — separate pure logic from pygame/OS I/O so it can be tested.
3. **Readability / onboarding** — small, navigable files.
4. **Packaging / distribution** — a real package with clean entry points and build.

## Constraints (decided during brainstorming)

- **Pure refactor:** behavior identical to today. No functional changes, no new
  features. Only relocation and mechanical adaptation of code.
- **Windows-only, but isolate OS code:** the launcher stays Windows-only
  (XInput, SendInput, registry, Steam/Epic paths). All OS calls are gathered
  into one isolation layer. We do NOT build a cross-platform abstraction
  (YAGNI — explicitly out of scope).
- **`python launcher.py` must keep working** at every step. `launcher.py`
  remains the entry point (a thin shim after the refactor).
- **The input-remap worker subprocess contract must be preserved.** The worker
  is spawned by re-invoking `launcher.py --input-remap-worker ...` (or the
  frozen exe with the same flag). The entry point must route this flag to the
  worker BEFORE starting pygame.

## Chosen approach

**Layered package `joypad/`** (chosen over a flat module split and over a
hexagonal/ports-and-adapters design). The flat split would not deliver clean
layering or the packaging goal; hexagonal is over-engineering given the
Windows-only decision.

OS isolation is pragmatic: a single `joypad/platform/windows.py` module holds
all ctypes/winreg/window/process code. No abstract interfaces.

## Target package layout

```
joypad-launcher/
├── launcher.py                 # thin shim: from joypad.app import main; sys.exit(main(sys.argv))
├── joypad/
│   ├── __init__.py             # package version
│   ├── app.py                  # main() + game loop (slimmed-down run_launcher)
│   │
│   ├── config/
│   │   ├── loader.py           # load_config / save_config
│   │   ├── theme.py            # _parse_color / _parse_font_* / _theme_from_config / _scale_theme_fonts_for_screen
│   │   └── settings.py         # build_settings_menu / apply_setting_toggle / _cycle_option / _on_off / toggles
│   │
│   ├── games/
│   │   ├── model.py            # game sections, categorization (_game_sections, build_categorized_game_list, build_tile_sections, _tile_selection_title)
│   │   ├── scan.py             # scan_libraries.py → steam/epic/nsp scanners (scan_all, scan_nsp_games)
│   │   └── scan_debug.py       # scanner diagnostics (moved as-is)
│   │
│   ├── covers/
│   │   ├── cache.py            # covers.py (CoverCache; image loading via pygame)
│   │   └── cdn.py              # cover_cdn.py (CdnCoverStore, nsp_cover_stems, CDN sources)
│   │
│   ├── launch/
│   │   └── launcher.py         # launch_steam/epic/nsp_game, _try_launch_game, perform_system_action, _ShellExecuteProcess
│   │
│   ├── input/
│   │   ├── profiles.py         # parse_*/format_* notation, load/save/merge/prepare_profile, assign/unassign, resolve_profile_path, default_chords
│   │   ├── bindings.py         # _build_keyboard_bindings, binding_label, cycle_binding/stick_mode
│   │   ├── engine.py           # run_remap_loop, XInput read, _send_input/_mouse_*/_key_event, deadzones
│   │   ├── watch.py            # _find_pids_*, game_process_alive, wait_for_game_exe_exit, game_watch_targets
│   │   ├── worker.py           # start_remap_worker, stop_remap_worker, run_remap_worker_main
│   │   └── log.py              # remap_log*, init_remap_log
│   │
│   ├── ui/
│   │   ├── fonts.py            # _wrap_words_to_width, _hard_break_word, _truncate_to_width
│   │   ├── background.py        # _load_background_surface (pygame), resolve_background_image, _background_enabled
│   │   ├── views/
│   │   │   ├── list.py         # build_list_layout, list navigation
│   │   │   └── tiles.py        # tile geometry/navigation/render (rebuild_tile_*, tile_move, compute_tile_grid, draw_tiles_view, _parse_tile_scale)
│   │   ├── overlay.py          # system menu / settings / "launching" overlay (rebuild_settings_layout, overlay_*, apply_setting_live)
│   │   └── editor.py           # input_remap_editor.py (InputRemapSession + helpers)
│   │
│   └── platform/
│       └── windows.py          # ALL ctypes/winreg/window/process-tree code
│                               #   _get_steam_path_from_registry, get_steam_path, _send_launcher_to_back,
│                               #   _bring_*_to_foreground, _get_process_and_descendant_pids, _yield_for_game_window,
│                               #   _wait_for_game_and_restore, _show_error_message
│                               # (pygame-based _load_background_surface goes to ui/background.py, not here)
│
├── ddcci/                      # unchanged (already a package)
├── tests/                      # new: pytest for pure logic
├── input_profiles/  assets/  config.example.json   # unchanged
├── requirements.txt            # runtime deps (unchanged content)
└── requirements-dev.txt        # new: pytest
```

### Layering rules

- **`launcher.py` stays the entry point.** `python launcher.py` behaves exactly
  as before; internally it calls `joypad.app.main(sys.argv)`.
- **`platform/windows.py` is the only place** with ctypes/winreg/window code.
  The rest of the package imports from it but makes no OS calls directly.
- **pygame lives only in `joypad/ui/` and `joypad/covers/cache.py`** (image
  loading). Config, profiles, scanning, and tile geometry stay pygame-free and
  are therefore testable.
- **`ddcci/` is not touched.**

## Decomposing `run_launcher()`

`run_launcher()` is ~1360 lines with ~40 nested functions sharing mutable state
through the closure (selection index, scroll, fonts, theme, screen, tile
geometry, active remap process, overlay flags, …). Functions cannot simply be
"moved out" — they read/write shared locals.

Strategy:

- Introduce **`AppState`** (a dataclass) holding the mutable session state:
  `config`, `theme`, games/sections, `selection`, `scroll_y`, `ui_mode`,
  `fonts`, active remap process, overlay flags. This replaces closure variables.
- Nested functions become **plain functions taking `state`** (and/or small pure
  helpers with no state), grouped into the modules above:
  - list geometry/navigation → `ui/views/list.py`
  - all tile functions → `ui/views/tiles.py`
  - menu/settings/overlays → `ui/overlay.py`
  - launch + window wait/restore orchestration → `app.py`, with low-level work
    in `launch/` and `platform/windows.py`
- Views MAY become light classes (`ListView`/`TilesView`) where methods read
  cleaner than passing `state`; default is functions-of-state.
- **`app.py`** keeps only: pygame init, the main `while` loop, event dispatch
  (gamepad/keyboard → navigation calls), and `draw_*` calls. The loop should
  read like a table of contents.

1:1 safety: pure geometric functions (`compute_tile_grid`, text wrapping) are
nearly stateless already — extract them first and cover with tests. State-bound
functions are moved mechanically, rewriting `var` → `state.var` only, with no
logic changes.

## Decomposing `input_remap.py`

| Module | Moves in | Deps |
|---|---|---|
| `profiles.py` | parse/format notation, load/save/merge/prepare_profile, assign/unassign, resolve_profile_path, default_chords | pure (json) — tested |
| `bindings.py` | _build_keyboard_bindings, binding_label, cycle_binding/stick_mode | pure — tested |
| `engine.py` | run_remap_loop, XInput read, _send_input/_mouse_*/_key_event, deadzones | Windows (ctypes) |
| `watch.py` | _find_pids_*, game_process_alive, wait_for_game_exe_exit, game_watch_targets | Windows (via platform/windows.py) |
| `worker.py` | start_remap_worker, stop_remap_worker, run_remap_worker_main | subprocess |
| `log.py` | remap_log*, init_remap_log | pure |

Note: the file currently has **two definitions** of `run_remap_loop` /
`wait_for_game_exe_exit` / `game_process_alive` — a Windows branch and
non-Windows fallback stubs guarded by `if sys.platform`. Both branches are kept
exactly as-is, just split between `engine.py`/`watch.py`. Behavior 1:1.

## Entry point — dual-mode

```python
# launcher.py  (thin shim, stays at repo root)
import sys
from joypad.app import main
sys.exit(main(sys.argv))
```

```python
# joypad/app.py
def main(argv):
    if len(argv) >= 2 and argv[1] == "--input-remap-worker":
        from joypad.input.worker import run_remap_worker_main
        run_remap_worker_main()
        return 0
    try:
        run()              # former run_launcher
        return 0
    except BaseException:
        # same behavior as today: write launcher_error.log + Windows MessageBox
        ...
        return 1
```

The worker spawn command (`[sys.executable, "launcher.py",
"--input-remap-worker", ...]` when not frozen; `[sys.executable, ...]` when
frozen) keeps working unchanged because the shim routes the flag. `_BASE_DIR`
(the directory next to launcher.py / the exe) is computed in one place and
passed into the package.

## Testing & 1:1 safety net

No tests exist today and the app is interactive, so the net is built around the
pure logic we are extracting anyway. It captures current behavior before the
move and re-runs the same tests after.

- **Tool:** `pytest`, added to `requirements-dev.txt` (not the runtime
  `requirements.txt`). Tests live in `tests/`.
- **Characterization (golden) tests written BEFORE the refactor**, importing the
  still-flat modules, using real data from `input_profiles/` and
  `config.example.json`:
  - `config/theme`: `_parse_color`, `_parse_font_*`, `_theme_from_config`,
    `_scale_theme_fonts_for_screen` — input→output table.
  - `input/profiles`: `parse → format` round-trip on both profiles in
    `input_profiles/`; `merge_profiles`, `resolve_profile_path`,
    `default_chords`.
  - `input/bindings`: `cycle_binding/stick_mode`, `binding_label`.
  - `games/model`: `_game_sections`, `build_categorized_game_list`,
    `build_tile_sections` on a synthetic game list.
  - `ui/fonts` + `compute_tile_grid`: text wrap/truncate and tile grid — pure
    geometry, asserted with concrete numbers (font object mocked via a `size()`
    function).
- **Not covered by automated tests:** pygame rendering, Windows API, real game
  launches, XInput. Their correctness is confirmed by a manual smoke run on
  Windows (the user) plus a static check that the code was moved mechanically.
- **Mechanical-move control:** for heavy OS functions, diff the moved body
  against the original — they must match line-for-line, changing only imports
  and the `state.` prefix. This is an explicit plan step, not "by eye".
- **Regression gate:** `import joypad`, a quick worker-flag dispatch check, and
  green `pytest` after each stage.

## Migration sequencing

Refactor in **stages, keeping `python launcher.py` runnable after each stage**
(not one big commit). Order goes leaf → core so imports always point "up".

1. **Scaffold + net.** Create the `joypad/` package (empty modules), `tests/`,
   `requirements-dev.txt`. Write golden tests against the still-flat modules.
   Green pytest. *App still runs the old way.*
2. **OS layer.** Move all ctypes/winreg/window/process-tree code from
   `launcher.py` and the Windows parts of `input_remap.py` into
   `joypad/platform/windows.py`. Flat files import from it. Smoke run.
3. **Leaf domains (no pygame):** `config/`, `games/` (incl. `scan_libraries` →
   `games/scan.py`), `covers/`, `launch/`, `input/`
   (profiles/bindings/log/engine/watch/worker). pytest + import check after
   each.
4. **UI layer:** `ui/fonts.py`, `views/list.py`, `views/tiles.py`,
   `overlay.py`, `editor.py` (former `input_remap_editor.py`).
5. **Core:** introduce `AppState`, slim `run_launcher` → `joypad/app.py:run()`,
   move nested functions into UI modules as functions-of-state. Dual-mode
   `main()`.
6. **Finalize:** `launcher.py` becomes the thin shim; delete the now-empty flat
   files; clean up the lazy imports.

## Build / CI updates (part of the refactor)

- `build_exe.bat`: replace the many `--hidden-import scan_libraries/covers/...`
  flags with `--collect-submodules joypad` (keep `--collect-submodules ddcci`);
  entry point stays `launcher.py`. Verify the worker flag works in frozen mode.
- `.github/workflows/release.yml`: same `--collect-submodules joypad`; add a
  `pytest` step before the build as a release gate.
- `--add-data` for `input_profiles` / `assets` / `config.example.json` stays.

## Out of scope

- Any new features or behavior changes.
- Cross-platform (Linux/macOS) support or platform abstraction interfaces.
- Refactoring `ddcci/`.
- Rewriting algorithms; only relocation + mechanical adaptation.
