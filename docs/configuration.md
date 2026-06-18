# Configuration reference

Complete description of `config.json`. Example: [config.example.json](../config.example.json).

## Top-level keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `steam_path` | string | — | Path to `steam.exe`. Auto-detected if omitted. |
| `steam_start_args` | string | `""` | Steam client args (e.g. `"-silent"`). Toggle in Settings. |
| `auto_scan` | bool | `false` | Scan Steam/Epic manifests and build the game list. |
| `games` | array | `[]` | Manual list or extra entries merged with scan results. |
| `theme` | object | — | Colors, fonts, UI mode, covers. |
| `fullscreen_args` | object | — | Launch args per platform: `steam`, `epic`, `twitch`. |
| `steam_skip_restore_ids` | array | `[]` | Steam App IDs that skip desktop restore after exit. |
| `twitch_roms_folder` | string | — | Folder scanned for `.nsp` files (Twitch). |
| `twitch_use_windows_association` | bool | `true` | Open `.nsp` via Windows file association. |
| `twitch_emulator_path` | string | — | Emulator executable when association is off. |
| `twitch_launch_args` | string | `""` | Extra args for Twitch launches. |
| `rawg_api_key` | string | — | Optional [RAWG](https://rawg.io/apidocs) API key for covers. |
| `input_remap` | object | — | Profile folder (see [input-remap.md](input-remap.md)). |
| `input_remap_games` | object | `{}` | Game → profile id mapping. |
| `ddcci` | object | — | Monitor power control via DDC/CI. |

Legacy `nsp_*` keys and `fullscreen_args.nsp` are still read if `twitch_*` keys are omitted.

---

## `theme`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `background` | `#RRGGBB` | `#14141c` | Background color. |
| `cursor` | `#RRGGBB` | `#4682c8` | Selection highlight. |
| `text` / `title` | `#RRGGBB` | — | Text colors. |
| `font_size_title` | number | `42` | Title font size. |
| `font_size_list` | number | `28` | List font size. |
| `font_size_hint` | number | `26` | Hint / footer font size. |
| `font_bold_title` / `font_bold_list` | bool | `true` | Bold fonts. |
| `background_image` | string | — | Background image (relative to launcher folder). |
| `auto_font_boost_low_res` | bool | `true` | Scale fonts up on short displays. |
| `auto_font_boost_ref_height` | number | `1080` | Reference height for font boost. |
| `auto_font_boost_max` | number | `1.65` | Max font boost multiplier. |
| `font_scale` | number | `1.0` | Global font scale. |
| `ui_mode` | `"list"` \| `"tiles"` | `"list"` | Main view mode. |
| `tile_scale` | number | `2.5` | Tile size in tiles mode (`1`–`9`, step 0.5). |
| `covers_folder` | string | `"covers"` | Local cover art folder. |
| `cdn_covers` | bool | `true` | Download missing covers to cache. |
| `cdn_cache_folder` | string | `"cover_cdn_cache"` | CDN cache directory. |

---

## `games[]` entries

| Field | Description |
|-------|-------------|
| `name` | Display name. |
| `platform` | `steam`, `epic`, `twitch`, or `system`. |
| `launch_args` | Command-line arguments. |
| `input_remap` | Optional profile id override. |

**Steam**

```json
{ "name": "Half-Life 2", "platform": "steam", "steam_app_id": "220", "launch_args": "-fullscreen" }
```

**Epic**

```json
{ "name": "Rocket League", "platform": "epic", "exe_path": "C:\\...\\RocketLeague.exe", "launch_args": "-fullscreen" }
```

**Twitch (`.nsp`)**

```json
{ "name": "Zelda", "platform": "twitch", "nsp_path": "\\\\server\\share\\game.nsp" }
```

Legacy `"platform": "nsp"` is still supported.

**System**

```json
{ "name": "Shutdown", "platform": "system", "system_action": "shutdown" }
```

Allowed `system_action` values: `"shutdown"`, `"reboot"`.

---

## Covers (tile mode)

Lookup order:

1. Files in `covers/` (name, app id, `steam_<id>`).
2. Steam `librarycache`.
3. CDN cache (`cdn_covers`): Steam CDN, Epic manifest, Libretro, Wikipedia; for Twitch — Title ID from `.nsp` filename.
4. Placeholder with platform label.

Toggle CDN in Settings → Appearance. Optional `rawg_api_key` adds another fallback.

---

## `ddcci`

| Key | Description |
|-----|-------------|
| `power_off_on_start` | Turn display off when a game starts. |
| `delay_ms` | Delay before the command (ms). |
| `log` | DDC/CI debug log. |

CLI flags (exe / `launcher.py`):

| Flag | Description |
|------|-------------|
| `--power-off-display` | Force display off on launch (Sunshine); ignores `power_off_on_start`. |
| `--power-off-only` | Power off display and exit; no UI. Uses `ddcci` monitor/log settings. |

Without flags, only `power_off_on_start: true` in config triggers power-off.

---

## `fullscreen_args`

```json
"fullscreen_args": {
  "steam": "-fullscreen",
  "epic": "-fullscreen",
  "twitch": ""
}
```

## Steam App ID

- [steamdb.info](https://steamdb.info/)
- Steam → Library → Manage → View store page — URL contains `app/XXXXX`
