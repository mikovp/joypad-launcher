"""Windows-only OS integration: registry, window focus, process trees."""

from joypad.platform.windows.hwnd import (
    _bring_any_other_window_to_foreground,
    _bring_launcher_to_front,
    _sleep_with_spinner,
    bring_game_to_foreground,
    bring_process_window_to_foreground,
    resize_launcher_window,
    send_launcher_to_back,
    show_error_message,
)
from joypad.platform.windows.process import (
    _get_process_and_descendant_pids,
    get_process_and_descendant_pids,
)
from joypad.platform.windows.registry import find_exe_in_uninstall_registry, get_steam_path
from joypad.platform.windows.wait import _yield_for_game_window, wait_for_game_and_restore

__all__ = [
    "_bring_any_other_window_to_foreground",
    "_bring_launcher_to_front",
    "_get_process_and_descendant_pids",
    "_sleep_with_spinner",
    "_yield_for_game_window",
    "bring_game_to_foreground",
    "bring_process_window_to_foreground",
    "find_exe_in_uninstall_registry",
    "get_process_and_descendant_pids",
    "get_steam_path",
    "resize_launcher_window",
    "send_launcher_to_back",
    "show_error_message",
    "wait_for_game_and_restore",
]
