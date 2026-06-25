"""UI mode and tile scale theme helpers."""

from joypad.config.theme.defaults import _TILE_SCALE_DEFAULT


_UI_MODES = ("home", "tiles", "list")


def ui_mode_from_theme(theme_section):
    v = (theme_section or {}).get("ui_mode")
    if isinstance(v, str):
        s = v.strip().lower()
        if s in _UI_MODES:
            return s
    return "home"


def ui_mode_label(mode):
    return {"home": "Home", "tiles": "Tiles", "list": "List"}.get(mode, "Home")


def parse_tile_scale(value, default=None):
    if default is None:
        default = _TILE_SCALE_DEFAULT
    if value is None:
        return default
    try:
        x = float(value)
        return max(0.5, min(9.0, x))
    except (TypeError, ValueError):
        return default
