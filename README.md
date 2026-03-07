# Joypad Launcher

<p align="center">
  <img src="anbernic_rg_40xx_h.jpg" alt="Joypad Launcher on Anbernic RG 40XX H" width="600">
</p>

**A game launcher for Steam and Epic Games, designed for handheld devices like Anbernic RG 40XX H that run Moonlight but have no touchscreen.** Navigate with D-pad or analog stick, launch games with a single button — no mouse or touch required.

Perfect for streaming from your PC via Moonlight + Sunshine: pick a game from the list using physical controls, then stream it to your handheld.

---

## Features

- **Gamepad-only UI** — D-pad, analog stick, A/B buttons
- **Steam & Epic Games** — auto-scans installed games or manual config
- **Fullscreen** — borderless window, ideal for streaming
- **Works with Sunshine** — add as an application for Moonlight clients

## Requirements

- Windows (Steam/Epic paths)
- Python 3.8+
- Gamepad (Xbox, DualShock, etc. — via pygame)
- Steam and/or Epic Games Launcher installed

## Quick Start

```bash
pip install -r requirements.txt
copy config.example.json config.json
python launcher.py
```

Set `"auto_scan": true` in `config.json` to auto-detect Steam and Epic games.

## Controls

| Action       | Gamepad                    | Keyboard        |
|-------------|----------------------------|-----------------|
| Select game | Left stick / D-pad up/down | Arrow keys      |
| Launch      | A or Start                 | Enter           |
| System menu | B or Back                  | Esc             |

## Configuration

1. Copy `config.example.json` to `config.json`.

2. **Auto-scan** (recommended): Set `"auto_scan": true`. The launcher finds Steam and Epic games from manifests.

3. **Manual list**: Set `"auto_scan": false` and add games to `games`:

```json
"games": [
  { "name": "Half-Life 2", "platform": "steam", "steam_app_id": "220", "launch_args": "-fullscreen" },
  { "name": "Rocket League", "platform": "epic", "exe_path": "C:\\Program Files\\Epic Games\\...\\RocketLeague.exe", "launch_args": "-fullscreen" }
]
```

### Theme

In `theme` you can set colors (`#RRGGBB`), font sizes, and `background_image`:

| Key                  | Description                    |
|----------------------|--------------------------------|
| `background`         | Background color               |
| `cursor`             | Selection highlight            |
| `text` / `title`     | Text colors                    |
| `font_size_title`    | Title font size (default 42)    |
| `font_size_list`     | List font size (default 28)     |
| `background_image`   | Custom background image path   |

## Build EXE

```bash
build_exe.bat
```

Output: `dist\JoypadLauncher.exe`. Copy `config.json` next to the exe.

## Resolution switching (QRes)

For streaming, you may want to change screen resolution before/after sessions. [**QRes**](https://sourceforge.net/projects/qres/) lets you do that from the command line.

**Download:** [QRes on SourceForge](https://sourceforge.net/projects/qres/) — place `QRes.exe` in the launcher folder (or add to PATH).

Example: `cmd /C path\to\QRes.exe /x:1280 /y:960` — set 1280×768. In Sunshine, use such commands in **Do** (on start) and **Undo** (on exit).

## Sunshine (Moonlight streaming)

Add Joypad Launcher as an application in Sunshine:

| Field   | Value                                      |
|---------|--------------------------------------------|
| Command | `cmd /C path\to\JoypadLauncher.exe`        |
| Working Directory | `path\to\dist`                    |

Use the exe path so Moonlight clients can launch it without Python.

## Steam App ID

- [steamdb.info](https://steamdb.info/) — search for a game to get its App ID
- Or: Steam → Library → right-click game → Manage → View store page — URL contains `app/XXXXX`

## License

MIT
