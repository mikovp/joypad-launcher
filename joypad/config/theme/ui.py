"""UI mode and tile scale theme helpers."""

from joypad.config.theme.defaults import _TILE_SCALE_DEFAULT


def ui_mode_from_theme(theme_section):
    v = (theme_section or {}).get("ui_mode")
    if isinstance(v, str) and v.strip().lower() == "tiles":
        return "tiles"
    return "list"


def ui_mode_label(mode):
    return "Tiles" if mode == "tiles" else "List"


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
