"""In-app settings menu and toggle handlers."""

from joypad.config.settings.menu import build_settings_menu
from joypad.config.settings.options import _TILE_SCALE_DEFAULT, _cycle_option
from joypad.config.settings.toggle import apply_setting_toggle

__all__ = [
    "_TILE_SCALE_DEFAULT",
    "_cycle_option",
    "apply_setting_toggle",
    "build_settings_menu",
]
