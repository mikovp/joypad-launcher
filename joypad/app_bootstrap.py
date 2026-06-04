"""Backward-compatible re-export; prefer ``joypad.bootstrap``."""

from joypad.bootstrap import BootResult, _build_game_row_numbers, bootstrap, collect_games
from joypad.bootstrap.constants import SYSTEM_MENU_ITEMS

__all__ = ["BootResult", "SYSTEM_MENU_ITEMS", "_build_game_row_numbers", "bootstrap", "collect_games"]
