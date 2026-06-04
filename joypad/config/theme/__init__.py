"""Theme colors, fonts, and UI mode from config."""

from joypad.config.theme.build import scale_theme_fonts_for_screen, theme_from_config
from joypad.config.theme.defaults import (
    _TILE_SCALE_DEFAULT,
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
from joypad.config.theme.ui import parse_tile_scale, ui_mode_from_theme, ui_mode_label

# Backward-compatible private aliases used by tests and legacy imports
_parse_color = parse_color
_parse_font_size = parse_font_size
_parse_font_bold = parse_font_bold
_parse_font_scale = parse_font_scale
_parse_positive_float = parse_positive_float

__all__ = [
    "BG_COLOR",
    "HIGHLIGHT_COLOR",
    "TEXT_COLOR",
    "TITLE_COLOR",
    "_TILE_SCALE_DEFAULT",
    "_parse_color",
    "_parse_font_bold",
    "_parse_font_size",
    "_parse_font_scale",
    "_parse_positive_float",
    "parse_tile_scale",
    "scale_theme_fonts_for_screen",
    "theme_from_config",
    "ui_mode_from_theme",
    "ui_mode_label",
]
