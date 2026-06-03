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

## Configuration reference

Complete reference for `config.json` and input-remap profile files (`input_profiles/*.json`).

### Top-level keys (`config.json`)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `steam_path` | string | — | Full path to `steam.exe`. Auto-detected if omitted. |
| `steam_start_args` | string | `""` | Extra args for the Steam client (e.g. `"-silent"`). Toggle in Settings. |
| `auto_scan` | bool | `false` | Scan Steam/Epic manifests and build the game list automatically. |
| `games` | array | `[]` | Manual game list when `auto_scan` is off, or extra entries merged with scan results. |
| `theme` | object | — | Colors, fonts, UI mode, covers (see below). |
| `fullscreen_args` | object | — | Default launch args per platform: `steam`, `epic`, `nsp`. |
| `steam_skip_restore_ids` | array | `[]` | Steam App IDs that skip desktop restore after exit (e.g. launchers that stay open). |
| `nsp_roms_folder` | string | — | UNC or local folder scanned for `.nsp` files (Switch). |
| `nsp_use_windows_association` | bool | `true` on Windows | Open `.nsp` via file association instead of `nsp_emulator_path`. |
| `nsp_emulator_path` | string | — | Emulator executable when association is off. |
| `nsp_launch_args` | string | `""` | Default extra args for NSP launch. |
| `rawg_api_key` | string | — | Optional [RAWG](https://rawg.io/apidocs) API key for cover fallback. |
| `input_remap` | object | — | Remap folder path (see below). |
| `input_remap_games` | object | `{}` | Maps each game to a profile id (see below). |
| `ddcci` | object | — | Monitor power via DDC/CI (see below). |

---

### `theme`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `background` | `#RRGGBB` | `#14141c` | Background color. |
| `cursor` | `#RRGGBB` | `#4682c8` | Selection highlight. |
| `text` | `#RRGGBB` | `#dcdce6` | Main text. |
| `title` | `#RRGGBB` | `#a0a0b4` | Secondary / title text. |
| `font_size_title` | number | `42` | Title font size. |
| `font_size_list` | number | `28` | List font size. |
| `font_size_hint` | number | `26` | Hint / footer font size. |
| `font_bold_title` | bool | `true` | Bold title font. |
| `font_bold_list` | bool | `true` | Bold list font. |
| `background_image` | string | — | Image path relative to launcher folder (e.g. `bg.jpg`). |
| `auto_font_boost_low_res` | bool | `true` | Scale fonts up on short displays. |
| `auto_font_boost_ref_height` | number | `1080` | Reference height for auto font boost. |
| `auto_font_boost_max` | number | `1.65` | Max font boost multiplier. |
| `font_scale` | number | `1.0` | Global font scale multiplier. |
| `ui_mode` | `"list"` \| `"tiles"` | `"list"` | Main view mode (also in Settings). |
| `tile_scale` | number | `2.5` | Tile size in tiles mode (`1`–`9`, steps of 0.5). |
| `covers_folder` | string | `"covers"` | Local cover art folder. |
| `cdn_covers` | bool | `true` | Download missing covers to cache. |
| `cdn_cache_folder` | string | `"cover_cdn_cache"` | CDN cache directory. |

---

### `games[]` — game entries

Common fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name. |
| `platform` | string | `steam`, `epic`, `nsp`, `twitch`, or `system`. |
| `launch_args` | string | Extra command-line args (overrides `fullscreen_args` default). |
| `input_remap` | string | Optional profile id override (same as `input_remap_games` entry). |

**Steam**

```json
{
  "name": "Half-Life 2",
  "platform": "steam",
  "steam_app_id": "220",
  "launch_args": "-fullscreen"
}
```

**Epic**

```json
{
  "name": "Rocket League",
  "platform": "epic",
  "exe_path": "C:\\Program Files\\Epic Games\\...\\RocketLeague.exe",
  "launch_args": "-fullscreen"
}
```

**Nintendo Switch (`.nsp`)**

```json
{
  "name": "Zelda",
  "platform": "nsp",
  "nsp_path": "\\\\server\\share\\game.nsp",
  "launch_args": ""
}
```

**System actions** (shutdown / reboot from the list)

```json
{
  "name": "Shutdown",
  "platform": "system",
  "system_action": "shutdown"
}
```

Allowed `system_action` values: `"shutdown"`, `"reboot"`.

---

### `input_remap` (launcher)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `profiles_dir` | string | `"input_profiles"` | Folder with profile JSON files (relative to launcher or absolute path). |

> **Note:** Deadzone and mouse sensitivity are **not** read from `config.json`. They live only in profile files (`input_profiles/*.json`).

---

### `input_remap_games` — assign profiles to games

When a game is launched on Windows, the launcher starts a remap worker if a profile is assigned.

Keys are stable game identifiers:

| Platform | Key format | Example |
|----------|------------|---------|
| Steam | `steam:<app_id>` | `"steam:220"` |
| Epic | `epic:<normalized_exe_path>` | `"epic:c:\\games\\duckov\\duckov.exe"` |
| NSP | `nsp:<normalized_nsp_path>` | `"nsp:\\\\share\\game.nsp"` |
| Other | `name:<game_name>` | `"name:My Game"` |

Values are **profile ids** (filename without `.json`):

```json
"input_remap_games": {
  "steam:3167020": "escape_from_duckov",
  "epic:c:\\games\\escape from duckov\\duckov.exe": "escape_from_duckov"
}
```

Profiles are created automatically in the editor or on first assignment. New files are copied from `default_wasd_mouse.json` with the game name.

**Visual editor:** Settings → **Controller mapping…** (or system menu). Saves to `input_profiles/<id>.json` and updates `input_remap_games`.

**Worker log:** `input_remap.log` next to the launcher (XInput status, SendInput errors, process watch).

Remapping is **Windows only** (XInput + SendInput). Epic games use process watch so remap survives launcher restarts.

---

### Profile files (`input_profiles/*.json`)

Each profile maps an Xbox-style gamepad to keyboard and mouse. All gameplay bindings come from the profile — not from hardcoded defaults in code.

**Template:** `input_profiles/default_wasd_mouse.json` — canonical default. When loading any other profile, missing fields are filled from this file (deep merge; game profile wins on conflicts).

#### Profile schema

| Field | Type | Default (template) | Description |
|-------|------|-------------------|-------------|
| `name` | string | `"WASD + mouse (default)"` | Display name in the editor. |
| `left_stick` | string | `"wasd"` | Left stick mode (see below). |
| `right_stick` | string | `"mouse"` | Right stick mode (see below). |
| `deadzone` | number | `0.25` | Stick deadzone `0.0`–`1.0`. Editor presets: `0.15`, `0.20`, `0.25`, `0.30`, `0.40`, `0.50`. |
| `mouse_sensitivity` | number | `10.0` | Mouse speed base. Editor presets: `6`, `8`, `10`, `12`, `16`, `20`, `28`. |
| `mouse_scale` | number | `2.5` | Multiplier applied with sensitivity (`gain = sensitivity × scale`). |
| `mouse_method` | string | `"both"` | How to move the cursor (see below). |
| `keyboard_method` | string | `"scancode"` | How to send keys (see below). |
| `buttons` | object | see template | Map button index → binding id. |
| `button_holds` | object | `{}` | Long-press alternate binding (see below). |
| `triggers` | object | — | Left/right trigger bindings. |
| `dpad` | object | — | D-pad direction bindings. |
| `stick_clicks` | object | — | L3 / R3 (stick press) bindings. |
| `chords` | object | — | LB/RB + face button layers (Steam Input style). |

#### Stick modes

| Field | Allowed values |
|-------|----------------|
| `left_stick` | `"none"`, `"wasd"`, `"arrows"` |
| `right_stick` | `"none"`, `"mouse"` |

#### `mouse_method`

| Value | Behavior |
|-------|----------|
| `"sendinput"` | Relative move via `SendInput` only. |
| `"cursor"` | Absolute move via `SetCursorPos` only. |
| `"both"` | Both (recommended for Unity and many PC games). |

#### `keyboard_method`

| Value | Behavior |
|-------|----------|
| `"scancode"` | Scan codes (recommended; works in most games). |
| `"vk"` | Virtual-key codes via `SendInput`. |
| `"both"` | Send scan code and VK together. |

#### Button names (`buttons`)

Use readable Xbox names as keys (legacy numeric `"0"`–`"7"` still accepted):

| Key | Button |
|-----|--------|
| `"a"` | A |
| `"b"` | B |
| `"x"` | X |
| `"y"` | Y |
| `"lb"` | LB (left bumper) |
| `"rb"` | RB (right bumper) |
| `"back"` | Back / View |
| `"start"` | Start / Menu |

Use `"none"` for unmapped buttons.

When **LB or RB is held**, face buttons A/B/X/Y use `chords.lb` / `chords.rb` instead of `buttons` (if chord binding is not `"none"`). While a chord is active, the bumper’s normal binding is suppressed.

#### Triggers (`triggers`)

| Key | Description |
|-----|-------------|
| `"left"` | LT (pressed when axis ≥ 30/255). |
| `"right"` | RT |

#### D-pad (`dpad`)

| Key | Direction |
|-----|-----------|
| `"dpad_up"` | Up |
| `"dpad_down"` | Down |
| `"dpad_left"` | Left |
| `"dpad_right"` | Right |

#### Stick clicks (`stick_clicks`)

| Key | Button |
|-----|--------|
| `"left"` | L3 (left stick press) |
| `"right"` | R3 (right stick press) |

Binding value: a string (hold while pressed) or an object for toggle:

```json
"stick_clicks": {
  "left": { "binding": "shift", "mode": "toggle" },
  "right": "v"
}
```

| `mode` | Behavior |
|--------|----------|
| `"hold"` | Default — key held while the stick is pressed. |
| `"toggle"` | Each press latches the key; next press releases it. |

#### Chords (`chords`)

Two layers (`lb`, `rb`), each with face keys `"a"`, `"b"`, `"x"`, `"y"`:

```json
"chords": {
  "lb": { "a": "3", "b": "4", "x": "none", "y": "none" },
  "rb": { "a": "5", "b": "6", "x": "7", "y": "8" }
}
```

#### Long press (`button_holds`)

Short tap uses `buttons`; hold past `hold_ms` switches to `hold`:

```json
"button_holds": {
  "b": {
    "hold": "tab",
    "hold_ms": 450
  }
}
```

- Key `"b"` = button B. Minimum `hold_ms`: 100.
- Only applies when the resolved binding equals the tap binding in `buttons`.

#### Binding ids

All slots accept the same binding ids (cycle through them in the editor):

| Category | Values |
|----------|--------|
| Empty | `"none"` |
| Mouse buttons | `"mouse_left"`, `"mouse_right"`, `"mouse_middle"` |
| Mouse wheel | `"mouse_wheel_up"`, `"mouse_wheel_down"` (one pulse on press) |
| Keys | `"space"`, `"enter"`, `"escape"`, `"tab"`, `"shift"`, `"ctrl"`, `"alt"` |
| Letters | `"w"`, `"a"`, `"s"`, `"d"`, `"e"`, `"r"`, `"f"`, `"t"`, `"q"`, `"g"`, `"m"`, `"i"`, `"v"`, `"z"`, `"c"` |
| Digits | `"0"`–`"9"` |

#### Example: full game profile

`input_profiles/escape_from_duckov.json` — Escape from Duckov (Epic/Steam):

```json
{
  "name": "Escape from Duckov",
  "left_stick": "wasd",
  "right_stick": "mouse",
  "deadzone": 0.25,
  "mouse_sensitivity": 10.0,
  "mouse_scale": 2.5,
  "mouse_method": "both",
  "keyboard_method": "scancode",
  "buttons": {
    "a": "f", "b": "escape", "x": "e", "y": "r",
    "lb": "1", "rb": "2", "back": "t", "start": "escape"
  },
  "button_holds": {
    "b": { "hold": "tab", "hold_ms": 450 }
  },
  "triggers": {
    "left": "mouse_right",
    "right": "mouse_left"
  },
  "dpad": {
    "dpad_up": "mouse_wheel_up",
    "dpad_down": "mouse_wheel_down",
    "dpad_left": "m",
    "dpad_right": "i"
  },
  "stick_clicks": {
    "left": { "binding": "shift", "mode": "toggle" },
    "right": "v"
  },
  "chords": {
    "lb": { "a": "3", "b": "4", "x": "none", "y": "none" },
    "rb": { "a": "5", "b": "6", "x": "7", "y": "8" }
  }
}
```

Profile ids are derived from the game name (`Escape from Duckov` → `escape_from_duckov`) or set manually in the editor.

---

### `ddcci`

Optional monitor power control when launching games:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `power_off_on_start` | bool | `false` | Turn display off via DDC/CI when a game starts. |
| `delay_ms` | number | `2000` | Delay before power-off command (ms). |
| `log` | bool | `false` | Write DDC/CI debug log. |

---

### `fullscreen_args`

Default launch arguments when a game entry has no `launch_args`:

```json
"fullscreen_args": {
  "steam": "-fullscreen",
  "epic": "-fullscreen",
  "nsp": ""
}
```

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
