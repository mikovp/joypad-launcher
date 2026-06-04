"""Build theme dict and scale fonts for screen height."""

from joypad.config.theme.defaults import (
    BG_COLOR,
    HIGHLIGHT_COLOR,
    TEXT_COLOR,
    TITLE_COLOR,
)
from joypad.config.theme.parse import (
    parse_color,
    parse_font_bold,
    parse_font_scale,
    parse_font_size,
    parse_positive_float,
)


def theme_from_config(config):
    """Returns theme colors and sizes dict from config (theme.*)."""
    theme = config.get("theme") or {}
    return {
        "background": parse_color(theme.get("background"), BG_COLOR),
        "cursor": parse_color(theme.get("cursor"), HIGHLIGHT_COLOR),
        "text": parse_color(theme.get("text"), TEXT_COLOR),
        "title": parse_color(theme.get("title"), TITLE_COLOR),
        "font_size_title": parse_font_size(theme.get("font_size_title") or theme.get("font_size_large"), 42, 12, 96),
        "font_size_list": parse_font_size(theme.get("font_size_list") or theme.get("font_size_small"), 28, 12, 72),
        "font_size_hint": (
            None
            if theme.get("font_size_hint") is None
            else parse_font_size(theme.get("font_size_hint"), 21, 8, 96)
        ),
        "font_bold_title": parse_font_bold(theme.get("font_bold_title"), False),
        "font_bold_list": parse_font_bold(theme.get("font_bold_list"), False),
    }


def scale_theme_fonts_for_screen(theme, theme_section, screen_height):
    """
    Scale fonts up when display height is below the reference (e.g. 1280×960 / streaming).
    """
    if not theme_section:
        theme_section = {}
    t = theme["font_size_title"]
    l = theme["font_size_list"]
    auto = theme_section.get("auto_font_boost_low_res")
    if auto is None:
        auto = True
    if auto and screen_height > 0:
        ref = parse_positive_float(theme_section.get("auto_font_boost_ref_height"), 1080.0)
        boost_max = parse_positive_float(theme_section.get("auto_font_boost_max"), 1.65)
        if screen_height < ref:
            factor = min(boost_max, ref / float(screen_height))
            t = int(round(t * factor))
            l = int(round(l * factor))
    mult = parse_font_scale(theme_section.get("font_scale"), 1.0)
    if mult != 1.0:
        t = int(round(t * mult))
        l = int(round(l * mult))
    theme["font_size_title"] = max(12, min(96, t))
    theme["font_size_list"] = max(12, min(72, l))
