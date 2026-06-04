# Architecture

Joypad Launcher is a Python app with a pygame UI. Entry point: `launcher.py` → `joypad.app.main()`.

## Package layout

```
joypad/
  app.py                 — main loop, worker dispatch
  app_state.py           — launcher mutable state
  bootstrap/             — init: games, display, constants
  config/                — config.json, theme, settings menu
  games/                 — game model, scanning
  covers/
    cache/               — local covers, Steam cache, placeholders
    cdn/                 — CDN cover downloads (Steam, Libretro, Wikipedia, RAWG)
  integrations/
    steam/ epic/ twitch/ vdf/   — platforms and VDF parsing
  launch/                — game launch, window focus, system actions
  input/
    profiles/            — JSON profiles, notation, paths, slots
    remap_engine/        — XInput → SendInput
    remap_loop/          — worker loop (Windows)
    sendinput/ xinput/   — Win32 injection and gamepad polling
    watch/               — game process watch
    worker/              — remap worker subprocess
  ui/
    loop/                — events, frame, poll, joysticks
    overlay/             — system/settings menu, launching spinner
    views/list/ tiles/   — list and tile views
    editor/              — visual remap editor
  platform/windows/      — registry, HWND, process tree, wait
ddcci/                   — DDC/CI (monitor power)
```

## Principles

- **Thin facades** — legacy import paths preserved (`app_bootstrap.py`, `ui/input_handler.py`, etc.).
- **Platform code** — Windows-only in `platform/`, `sendinput/`, `xinput/`, `watch/`; lazy imports or stubs elsewhere.
- **Twitch** — former NSP integration; config keys `twitch_*` with fallback to `nsp_*`.

## CI

GitHub Actions: `pytest`, `ruff`, `mypy` (see `.github/workflows/ci.yml`).

## Refactor summary (2026)

Monolithic modules were split into packages with `__init__.py` re-exports. Main moves:

| Was (single file) | Now (package) |
|-------------------|---------------|
| `app_bootstrap.py` | `bootstrap/` |
| `covers/cache.py` | `covers/cache/` |
| `covers/cdn.py` | `covers/cdn/` + `sources/` |
| `config/settings.py`, `theme.py` | `config/settings/`, `config/theme/` |
| `integrations/steam|epic|twitch.py` | `integrations/*/` |
| `integrations/vdf.py` | `integrations/vdf/` |
| `input/engine.py` (watch) | `input/watch/` |
| `input/worker.py` | `input/worker/` |
| `input/remap_engine.py` | `input/remap_engine/` |
| `input/remap_loop.py` | `input/remap_loop/win32/` |
| `input/sendinput.py`, `xinput.py` | `sendinput/`, `xinput/` |
| `input/profiles.py` | `input/profiles/` + `notation/` |
| `platform/windows.py` | `platform/windows/` |
| `ui/input_handler.py` | `ui/loop/` |
| `ui/overlay.py` | `ui/overlay/` + `menu/` |
| `ui/views/list.py`, `tiles.py` | `views/list/`, `views/tiles/navigation/` |
| `ui/editor/*` | `editor/slots/`, `drawing/pad/`, `drawing/grid/`, `input/` |
| `launch/launcher.py` | `launch/` (system, start, focus) |

Behavior and consumer imports are unchanged; 76 tests pass.
