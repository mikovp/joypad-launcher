"""Settings option lists and small helpers."""

import os
import sys

from joypad.config.twitch import get_twitch_use_windows_association
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


def _twitch_association_on(config):
    val = get_twitch_use_windows_association(config)
    if val is None:
        return sys.platform == "win32"
    return val
