# Default colors (overridden from config.json → theme)
BG_COLOR = (20, 20, 28)
TEXT_COLOR = (220, 220, 230)
HIGHLIGHT_COLOR = (70, 130, 200)
TITLE_COLOR = (160, 160, 180)


def _parse_color(value, default):
    """Converts config value to (R, G, B) tuple.
    value: string #RRGGBB / #RGB or list [r,g,b] (0-255).
    """
    if value is None:
        return default
    # Hex: "#1a1a1c" or "1a1a1c", short "#fff" -> #ffffff
    if isinstance(value, str):
        s = value.strip().lstrip("#")
        try:
            if len(s) == 6:
                r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
                return (r, g, b)
            if len(s) == 3:
                r = int(s[0], 16) * 17
                g = int(s[1], 16) * 17
                b = int(s[2], 16) * 17
                return (r, g, b)
        except (ValueError, IndexError):
            pass
        return default
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            r, g, b = int(value[0]), int(value[1]), int(value[2])
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return (r, g, b)
        except (TypeError, ValueError):
            pass
    return default


def _parse_font_size(value, default, min_size=12, max_size=120):
    """Returns font size (int) from config."""
    if value is None:
        return default
    try:
        size = int(value)
        return max(min_size, min(max_size, size))
    except (TypeError, ValueError):
        return default


def _parse_font_bold(value, default=False):
    """Returns True for bold font, False for normal."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("bold", "true", "1", "yes"):
            return True
        if s in ("normal", "regular", "false", "0", "no"):
            return False
    return default


def _parse_font_scale(value, default=1.0):
    """Positive font size multiplier from theme.font_scale."""
    if value is None:
        return default
    try:
        x = float(value)
        return x if x > 0 else default
    except (TypeError, ValueError):
        return default


def _parse_positive_float(value, default):
    if value is None:
        return default
    try:
        x = float(value)
        return x if x > 0 else default
    except (TypeError, ValueError):
        return default


def theme_from_config(config):
    """Returns theme colors and sizes dict from config (theme.*)."""
    theme = config.get("theme") or {}
    return {
        "background": _parse_color(theme.get("background"), BG_COLOR),
        "cursor": _parse_color(theme.get("cursor"), HIGHLIGHT_COLOR),
        "text": _parse_color(theme.get("text"), TEXT_COLOR),
        "title": _parse_color(theme.get("title"), TITLE_COLOR),
        "font_size_title": _parse_font_size(theme.get("font_size_title") or theme.get("font_size_large"), 42, 12, 96),
        "font_size_list": _parse_font_size(theme.get("font_size_list") or theme.get("font_size_small"), 28, 12, 72),
        "font_size_hint": (
            None
            if theme.get("font_size_hint") is None
            else _parse_font_size(theme.get("font_size_hint"), 21, 8, 96)
        ),
        "font_bold_title": _parse_font_bold(theme.get("font_bold_title"), False),
        "font_bold_list": _parse_font_bold(theme.get("font_bold_list"), False),
    }


def scale_theme_fonts_for_screen(theme, theme_section, screen_height):
    """
    Scale fonts up when display height is below the reference (e.g. 1280×960 / streaming).
    Default: if height < auto_font_boost_ref_height (1080), multiply by ref/height, capped at auto_font_boost_max.
    Then multiply by theme.font_scale for manual tuning.
    """
    if not theme_section:
        theme_section = {}
    t = theme["font_size_title"]
    l = theme["font_size_list"]
    auto = theme_section.get("auto_font_boost_low_res")
    if auto is None:
        auto = True
    if auto and screen_height > 0:
        ref = _parse_positive_float(theme_section.get("auto_font_boost_ref_height"), 1080.0)
        boost_max = _parse_positive_float(theme_section.get("auto_font_boost_max"), 1.65)
        if screen_height < ref:
            factor = min(boost_max, ref / float(screen_height))
            t = int(round(t * factor))
            l = int(round(l * factor))
    mult = _parse_font_scale(theme_section.get("font_scale"), 1.0)
    if mult != 1.0:
        t = int(round(t * mult))
        l = int(round(l * mult))
    theme["font_size_title"] = max(12, min(96, t))
    theme["font_size_list"] = max(12, min(72, l))


def ui_mode_from_theme(theme_section):
    v = (theme_section or {}).get("ui_mode")
    if isinstance(v, str) and v.strip().lower() == "tiles":
        return "tiles"
    return "list"


def ui_mode_label(mode):
    return "Tiles" if mode == "tiles" else "List"


_TILE_SCALE_DEFAULT = 2.5


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
