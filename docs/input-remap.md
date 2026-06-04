# Input remap (gamepad → keyboard/mouse)

**Windows only** (XInput + SendInput). When a game with an assigned profile is launched, a separate worker process starts.

## Launcher setup

**Settings → Controller mapping…** (or System menu) — visual editor. Saves `input_profiles/<id>.json` and updates `input_remap_games`.

Worker log: `input_remap.log` next to the launcher.

## `input_remap` in config.json

| Key | Default | Description |
|-----|---------|-------------|
| `profiles_dir` | `"input_profiles"` | Folder with JSON profile files. |

Deadzone and mouse sensitivity are set **only in profile files**, not in config.

## `input_remap_games`

Keys are stable game identifiers:

| Platform | Key format |
|----------|------------|
| Steam | `steam:<app_id>` |
| Epic | `epic:<normalized_exe_path>` |
| Twitch | `twitch:<normalized_nsp_path>` |
| Other | `name:<game_name>` |

Value is the **profile id** (filename without `.json`):

```json
"input_remap_games": {
  "steam:3167020": "escape_from_duckov"
}
```

New profiles are copied from `input_profiles/default_wasd_mouse.json`.

---

## Profile schema (`input_profiles/*.json`)

| Field | Default (template) | Description |
|-------|-------------------|-------------|
| `name` | `"WASD + mouse (default)"` | Display name in the editor. |
| `left_stick` | `"wasd"` | `none`, `wasd`, `arrows`. |
| `right_stick` | `"mouse"` | `none`, `mouse`. |
| `deadzone` | `0.25` | 0.0–1.0. |
| `mouse_sensitivity` | `10.0` | Base mouse speed. |
| `mouse_scale` | `2.5` | Multiplier (`gain = sensitivity × scale`). |
| `mouse_method` | `"both"` | `sendinput`, `cursor`, `both`. |
| `keyboard_method` | `"scancode"` | `scancode`, `vk`, `both`. |
| `buttons` | see template | Button → binding id. |
| `button_holds` | `{}` | Long-press alternate binding. |
| `triggers` | — | LT / RT. |
| `dpad` | — | D-pad directions. |
| `stick_clicks` | — | L3 / R3. |
| `chords` | — | LB/RB + face buttons (Steam Input style). |

### Button names (`buttons`)

| Key | Button |
|-----|--------|
| `a`, `b`, `x`, `y` | Face buttons |
| `lb`, `rb` | Bumpers |
| `back`, `start` | View / Menu |

Legacy numeric `"0"`–`"7"` is accepted. Use `"none"` for unmapped buttons.

When **LB or RB is held**, face buttons use bindings from `chords.lb` / `chords.rb` instead of `buttons`.

### Stick clicks (toggle)

```json
"stick_clicks": {
  "left": { "binding": "shift", "mode": "toggle" },
  "right": "v"
}
```

### Long press (`button_holds`)

```json
"button_holds": {
  "b": { "hold": "tab", "hold_ms": 450 }
}
```

Minimum `hold_ms`: 100.

### Binding ids

| Category | Values |
|----------|--------|
| Empty | `none` |
| Mouse | `mouse_left`, `mouse_right`, `mouse_middle`, `mouse_wheel_up`, `mouse_wheel_down` |
| Keys | `space`, `enter`, `escape`, `tab`, `shift`, `ctrl`, `alt`, letters, `0`–`9` |

### Example profiles

See `input_profiles/default_wasd_mouse.json` and any game-specific files (e.g. `escape_from_duckov.json`).

For Epic games, the worker watches the game process by exe/folder and survives Epic launcher restarts.
