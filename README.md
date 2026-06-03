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

| Action       | Gamepad (list)             | Gamepad (tiles)              | Keyboard        |
|-------------|----------------------------|------------------------------|-----------------|
| Select game | Stick / D-pad ↑↓           | Stick / D-pad ↑↓←→           | Arrows          |
| Libraries   | —                          | LB / RB (Steam, Epic, …)     | —               |
| Scroll page | LT / RT, LB / RB           | LT / RT                      | PgUp / PgDn     |
| Launch      | A or Start                 | A or Start                   | Enter           |
| System menu | B or Back                  | B or Back                    | Esc             |

Switch **List** / **Tiles** in Settings → Appearance → **View**.

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
| `ui_mode`            | `list` or `tiles` (also in Settings) |
| `tile_scale`         | Tile size in tiles mode: `1`–`9` in 10 steps (default `2.5`) |
| `covers_folder`      | Folder for custom covers (default `covers`) |
| `cdn_covers`         | Download missing art to disk cache (default on) |
| `cdn_cache_folder`   | CDN cache directory (default `cover_cdn_cache`) |

### Tile view and covers

With `ui_mode: "tiles"`, games appear as **square tiles** in a grid (several per row, rows below). **Steam**, **Epic Games**, and **Nintendo Switch** blocks are shown one after another on the same scrollable page. The selected game shows a large cover on top.

Cover lookup order:

1. **Your files** — `covers/` (e.g. `220.jpg`, game name).
2. **Steam library cache** — `steam/appcache/librarycache/`.
3. **Free CDN cache** (`cdn_covers` on) — downloads once into `cover_cdn_cache/`, **no API key**:
   - **Steam** — Steam CDN by app id.
   - **Epic / other** — Epic manifest image (if any); Libretro + Steam search + Wikipedia by game name.
   - **Switch (.nsp)** — by **`.nsp` filename**: cover from **Title ID** in the name (`[01004A001E32E000]` → tinfoil.media), then Libretro, Steam search (with `S.T.A.L.K.E.R.` style aliases), Wikipedia.
4. **Placeholder** — colored tile with platform label.

Optional `rawg_api_key` in config adds one more fallback via [RAWG](https://rawg.io/apidocs) (registration required).

Toggle **CDN covers** in Settings → Appearance. First launch may show placeholders briefly; art fills in as downloads finish.

## Build EXE

```bash
build_exe.bat
```

Output: `dist\JoypadLauncher.exe`. Copy `config.json` next to the exe.

## Resolution switching (QRes)

For streaming, you may want to change screen resolution before/after sessions. [**QRes**](https://sourceforge.net/projects/qres/) lets you do that from the command line.

**Download:** [QRes on SourceForge](https://sourceforge.net/projects/qres/) — place `QRes.exe` in the launcher folder (or add to PATH).

In Sunshine, use QRes in **Do** (on start) and **Undo** (on exit). Examples (adjust paths to your install folder):

```text
cmd /C C:\path\to\JoypadLauncher\QRes.exe /x:1280 /y:960
cmd /C C:\path\to\JoypadLauncher\QRes.exe /x:3840 /y:1080 /r:144
```

The first sets 1280×960 for the streaming session; the second restores 3840×1080 at 144 Hz when the session ends.

## Sunshine (Moonlight streaming)

Add Joypad Launcher as an application in Sunshine:

| Field   | Value                                      |
|---------|--------------------------------------------|
| Command | `cmd /C path\to\JoypadLauncher.exe`        |
| Working Directory | `path\to\dist`                    |

Use the exe path so Moonlight clients can launch it without Python.

### Example: Do / Undo commands

If the PC is on the lock screen (`logonui`), reconnect the session to the physical console before launching. Put this in **Do** (or run it before the launcher command):

```powershell
powershell -NoProfile -ExecutionPolicy unrestricted -Command "if (tasklist | findstr -i logonui) { tsdiscon ((quser $env:USERNAME | select -Skip 1) -split '\s+')[2]; Start-Sleep 1; tscon ((quser $env:USERNAME | select -Skip 1) -split '\s+')[1] /dest:console; New-Item -Path '$env:TEMP\apollo_unlock.lock' -ItemType File -Force; exit 1; }"
```

Combine with QRes in **Do** / **Undo** as needed:

| When   | Example command |
|--------|-----------------|
| **Do** | `cmd /C C:\path\to\JoypadLauncher\QRes.exe /x:1280 /y:960` |
| **Undo** | `cmd /C C:\path\to\JoypadLauncher\QRes.exe /x:3840 /y:1080 /r:144` |

## Steam App ID

- [steamdb.info](https://steamdb.info/) — search for a game to get its App ID
- Or: Steam → Library → right-click game → Manage → View store page — URL contains `app/XXXXX`

## License

MIT
