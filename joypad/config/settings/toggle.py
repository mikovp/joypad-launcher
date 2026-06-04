"""Apply setting toggles and persist config."""

from joypad.config.loader import save_config
from joypad.config.settings.options import (
    _DDCCI_DELAY_OPTIONS,
    _FONT_SCALE_OPTIONS,
    _FONT_SIZE_HINT_OPTIONS,
    _FONT_SIZE_LIST_OPTIONS,
    _FONT_SIZE_TITLE_OPTIONS,
    _TILE_SCALE_DEFAULT,
    _TILE_SCALE_OPTIONS,
    _background_enabled,
    _cycle_option,
    _steam_silent_on,
    _twitch_association_on,
)
from joypad.config.theme import parse_tile_scale, ui_mode_from_theme
from joypad.config.twitch import set_twitch_use_windows_association


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
    elif key == "twitch_association":
        set_twitch_use_windows_association(config, not _twitch_association_on(config))
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
