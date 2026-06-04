"""Windows process watch helpers for remap worker and launcher."""

import sys

if sys.platform == "win32":
    from joypad.input.watch.win32.find import find_pids_in_directory
    from joypad.input.watch.win32.game import (
        active_game_pids,
        game_process_alive,
        wait_for_game_exe_exit,
    )
    from joypad.input.watch.win32.process import (
        alive_pids,
        any_pid_alive,
        get_process_tree_pids,
    )

    _active_game_pids = active_game_pids
    _alive_pids = alive_pids
    _any_pid_alive = any_pid_alive
    _find_pids_in_directory = find_pids_in_directory
    _get_process_tree_pids = get_process_tree_pids
else:
    from joypad.input.watch.win32.stubs import (
        active_game_pids as _active_game_pids,
    )
    from joypad.input.watch.win32.stubs import (
        alive_pids as _alive_pids,
    )
    from joypad.input.watch.win32.stubs import (
        any_pid_alive as _any_pid_alive,
    )
    from joypad.input.watch.win32.stubs import (
        find_pids_in_directory as _find_pids_in_directory,
    )
    from joypad.input.watch.win32.stubs import (
        game_process_alive,
        wait_for_game_exe_exit,
    )
    from joypad.input.watch.win32.stubs import (
        get_process_tree_pids as _get_process_tree_pids,
    )

__all__ = [
    "_active_game_pids",
    "_alive_pids",
    "_any_pid_alive",
    "_find_pids_in_directory",
    "_get_process_tree_pids",
    "game_process_alive",
    "wait_for_game_exe_exit",
]
