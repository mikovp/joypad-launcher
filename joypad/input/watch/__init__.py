"""Process watch helpers for remap worker and launcher game-exit detection."""

from joypad.input.watch.targets import game_watch_targets
from joypad.input.watch.win32 import (
    _active_game_pids,
    _alive_pids,
    _any_pid_alive,
    _find_pids_in_directory,
    _get_process_tree_pids,
    game_process_alive,
    wait_for_game_exe_exit,
)

__all__ = [
    "_active_game_pids",
    "_alive_pids",
    "_any_pid_alive",
    "_find_pids_in_directory",
    "_get_process_tree_pids",
    "game_process_alive",
    "game_watch_targets",
    "wait_for_game_exe_exit",
]
