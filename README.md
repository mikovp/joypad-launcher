# Joypad Launcher

<p align="center">
  <img src="anbernic_rg_40xx_h.jpg" alt="Joypad Launcher on Anbernic RG 40XX H" width="600">
</p>

A **gamepad-only** launcher for **Steam**, **Epic**, and **Twitch (.nsp)** games — no mouse or touchscreen required. Built for handhelds (Anbernic RG and similar) with **Moonlight + Sunshine**: pick a game on the stream client and launch with one button.

## Features

- Gamepad UI — D-pad, sticks, A/B, LB/RB, LT/RT
- Auto-scan Steam and Epic (or manual game list)
- **List** and **tiles** views with cover art
- Borderless fullscreen window
- Gamepad → keyboard/mouse remap (Windows)
- Shutdown / reboot from the system menu

## Requirements

- **Windows** (Steam, Epic, input remap)
- Python 3.8+ (or the bundled `.exe`)
- Gamepad (Xbox, DualShock, etc. via pygame)
- Steam and/or Epic Games Launcher installed

## Quick start

```bash
pip install -r requirements.txt
copy config.example.json config.json
python launcher.py
```

Set `"auto_scan": true` in `config.json` to detect Steam and Epic games automatically.

**Standalone exe:** run `build_exe.bat` → `dist\JoypadLauncher.exe` (place `config.json` next to the exe).

## Controls

| Action | List | Tiles | Keyboard |
|--------|------|-------|----------|
| Select | Stick / D-pad ↑↓ | Stick / D-pad ↑↓←→ | Arrows |
| Libraries | — | LB / RB | — |
| Page scroll | LT / RT | LT / RT | PgUp / PgDn |
| Launch | A or Start | A or Start | Enter |
| System menu | B or Back | B or Back | Esc |

Switch **List / Tiles**: Settings → Appearance → **View**.

## Configuration

1. Copy `config.example.json` to `config.json`.
2. **auto_scan** — automatic game list.
3. **theme** — colors, fonts, background, tile size.
4. **input_remap** — gamepad profiles (editor in Settings).

More detail:

- [docs/configuration.md](docs/configuration.md) — full `config.json` reference, covers, theme
- [docs/input-remap.md](docs/input-remap.md) — profiles and mapping editor
- [docs/streaming.md](docs/streaming.md) — Sunshine, Moonlight, QRes

## Documentation

| Audience | Link |
|----------|------|
| Users | [docs/README.md](docs/README.md) |
| Developers | [docs/development.md](docs/development.md), [docs/architecture.md](docs/architecture.md) |

## Roadmap

Planned improvements (no fixed release dates):

- [ ] **Cursor control in the launcher** — virtual mouse cursor driven by the gamepad
- [ ] **Application localization** — UI strings and settings in multiple languages
- [ ] **Game search and filtering** — find titles quickly in large libraries
- [ ] **On-screen keyboard** — text input from the gamepad (needed for search without a physical keyboard)
- [ ] **Favorites and recently played** — pin and revisit games from the main view
- [ ] **More storefronts** — GOG Galaxy and other PC library sources

## License

MIT
