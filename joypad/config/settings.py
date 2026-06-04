import os
import sys

from joypad.config.loader import save_config
from joypad.config.theme import parse_tile_scale, ui_mode_from_theme, ui_mode_label
from joypad.paths import _BASE_DIR

_FONT_SCALE_OPTIONS = [1.0, 1.08, 1.15, 1.25, 1.35, 1.5]
_TILE_SCALE_OPTIONS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 9.0]
_TILE_SCALE_DEFAULT = 2.5
_DDCCI_DELAY_OPTIONS = [1000, 2000, 3000, 5000]
_FONT_SIZE_TITLE_OPTIONS = [42, 46, 52, 58, 64]
_FONT_SIZE_LIST_OPTIONS = [28, 32, 38, 44, 50]
_FONT_SIZE_HINT_OPTIONS = [None, 21, 26, 32]


def _cycle_option(current, options):
    for i, val in enumerate(options):
        if val is None and current is None:
            return options[(i + 1) % len(options)]
        if val == current or (isinstance(current, float) and isinstance(val, (int, float)) and abs(val - current) < 0.001):
            return options[(i + 1) % len(options)]
    return options[0]


def _on_off(value):
    return "On" if value else "Off"


def _background_enabled(config):
    theme = config.get("theme") or {}
    val = theme.get("background_image")
    if val is False:
        return False
    if isinstance(val, str) and val.strip():
        return True
    return os.path.isfile(os.path.join(_BASE_DIR, "bg.jpg"))


def _steam_silent_on(config):
    return "-silent" in (config.get("steam_start_args") or "")


def _nsp_association_on(config):
    val = config.get("nsp_use_windows_association")
    if val is None:
        return sys.platform == "win32"
    return bool(val)


def build_settings_menu(config):
    """Settings menu rows with category headers (kind: header | setting | action)."""
    ddcci = config.get("ddcci") or {}
    remap = config.get("input_remap") or {}
    theme = config.get("theme") or {}
    delay = int(ddcci.get("delay_ms", 2000))
    scale = float(theme.get("font_scale", 1.0) or 1.0)
    tile_scale = parse_tile_scale(theme.get("tile_scale"), _TILE_SCALE_DEFAULT)
    title_sz = int(theme.get("font_size_title") or 42)
    list_sz = int(theme.get("font_size_list") or 28)
    hint_sz = theme.get("font_size_hint")
    hint_label = "Auto" if hint_sz is None else str(int(hint_sz))
    sections = [
        ("Monitor", [
            ("ddcci_power", "Off on start: %s" % _on_off(ddcci.get("power_off_on_start"))),
            ("ddcci_delay", "Off delay: %d ms" % delay),
            ("ddcci_log", "Debug log: %s" % _on_off(ddcci.get("log"))),
        ]),
        ("Appearance", [
            ("ui_mode", "View: %s" % ui_mode_label(ui_mode_from_theme(theme))),
            ("tile_scale", "Tile scale: %.2f" % tile_scale),
            ("background", "Background: %s" % _on_off(_background_enabled(config))),
            ("font_scale", "Font scale: %.2f" % scale),
            ("font_size_title", "Title size: %d" % title_sz),
            ("font_size_list", "List size: %d" % list_sz),
            ("font_size_hint", "Hint size: %s" % hint_label),
            ("font_bold_title", "Bold title: %s" % _on_off(theme.get("font_bold_title"))),
            ("font_bold_list", "Bold list: %s" % _on_off(theme.get("font_bold_list"))),
            ("auto_font_boost", "Low-res boost: %s" % _on_off(theme.get("auto_font_boost_low_res", True))),
            ("cdn_covers", "CDN covers: %s" % _on_off(theme.get("cdn_covers", True))),
        ]),
        ("Games & launch", [
            ("auto_scan", "Auto-scan: %s" % _on_off(config.get("auto_scan"))),
            ("steam_silent", "Steam silent: %s" % _on_off(_steam_silent_on(config))),
            ("nsp_association", "NSP via Windows: %s" % _on_off(_nsp_association_on(config))),
        ]),
    ]
    items = []
    for section_title, rows in sections:
        items.append({"kind": "header", "title": section_title})
        for key, label in rows:
            items.append({"kind": "setting", "key": key, "label": label})
    items.append({"kind": "header", "title": "Controller"})
    items.append(
        {
            "kind": "setting",
            "key": "input_remap_log",
            "label": "Remap log: %s" % _on_off(remap.get("log")),
        }
    )
    items.append({"kind": "action", "key": "input_remap_open", "label": "Controller mapping…"})
    items.append({"kind": "action", "key": "back", "label": "Back"})
    return items


def apply_setting_toggle(config, key):
    """Toggle/cycle a setting and save config. Returns True if changed."""
    if key == "back":
        return False
    if key == "ddcci_power":
        ddcci = config.setdefault("ddcci", {})
        ddcci["power_off_on_start"] = not bool(ddcci.get("power_off_on_start"))
    elif key == "ddcci_delay":
        ddcci = config.setdefault("ddcci", {})
        cur = int(ddcci.get("delay_ms", 2000))
        ddcci["delay_ms"] = _cycle_option(cur, _DDCCI_DELAY_OPTIONS)
    elif key == "ui_mode":
        theme = config.setdefault("theme", {})
        theme["ui_mode"] = "tiles" if ui_mode_from_theme(theme) == "list" else "list"
    elif key == "tile_scale":
        theme = config.setdefault("theme", {})
        cur = parse_tile_scale(theme.get("tile_scale"), _TILE_SCALE_DEFAULT)
        theme["tile_scale"] = _cycle_option(cur, _TILE_SCALE_OPTIONS)
    elif key == "background":
        theme = config.setdefault("theme", {})
        if _background_enabled(config):
            theme["background_image"] = False
        else:
            theme["background_image"] = "bg.jpg"
    elif key == "font_scale":
        theme = config.setdefault("theme", {})
        cur = float(theme.get("font_scale", 1.0) or 1.0)
        theme["font_scale"] = _cycle_option(cur, _FONT_SCALE_OPTIONS)
    elif key == "font_size_title":
        theme = config.setdefault("theme", {})
        cur = int(theme.get("font_size_title") or 42)
        theme["font_size_title"] = _cycle_option(cur, _FONT_SIZE_TITLE_OPTIONS)
    elif key == "font_size_list":
        theme = config.setdefault("theme", {})
        cur = int(theme.get("font_size_list") or 28)
        theme["font_size_list"] = _cycle_option(cur, _FONT_SIZE_LIST_OPTIONS)
    elif key == "font_size_hint":
        theme = config.setdefault("theme", {})
        cur = theme.get("font_size_hint")
        if cur is not None:
            cur = int(cur)
        theme["font_size_hint"] = _cycle_option(cur, _FONT_SIZE_HINT_OPTIONS)
    elif key == "font_bold_title":
        theme = config.setdefault("theme", {})
        theme["font_bold_title"] = not bool(theme.get("font_bold_title"))
    elif key == "font_bold_list":
        theme = config.setdefault("theme", {})
        theme["font_bold_list"] = not bool(theme.get("font_bold_list"))
    elif key == "auto_font_boost":
        theme = config.setdefault("theme", {})
        cur = theme.get("auto_font_boost_low_res")
        if cur is None:
            cur = True
        theme["auto_font_boost_low_res"] = not bool(cur)
    elif key == "cdn_covers":
        theme = config.setdefault("theme", {})
        cur = theme.get("cdn_covers")
        if cur is None:
            cur = True
        theme["cdn_covers"] = not bool(cur)
    elif key == "auto_scan":
        config["auto_scan"] = not bool(config.get("auto_scan"))
    elif key == "steam_silent":
        if _steam_silent_on(config):
            config["steam_start_args"] = ""
        else:
            config["steam_start_args"] = "-silent"
    elif key == "nsp_association":
        config["nsp_use_windows_association"] = not _nsp_association_on(config)
    elif key == "ddcci_log":
        ddcci = config.setdefault("ddcci", {})
        ddcci["log"] = not bool(ddcci.get("log"))
    elif key == "input_remap_log":
        remap = config.setdefault("input_remap", {})
        remap["log"] = not bool(remap.get("log"))
    else:
        return False
    save_config(config)
    return True
