"""Build the in-app settings menu structure."""

from joypad.config.settings.options import (
    _TILE_SCALE_DEFAULT,
    _background_enabled,
    _on_off,
    _steam_silent_on,
    _twitch_association_on,
)
from joypad.config.theme import parse_tile_scale, ui_mode_from_theme, ui_mode_label


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
            ("twitch_association", "Twitch via Windows: %s" % _on_off(_twitch_association_on(config))),
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
