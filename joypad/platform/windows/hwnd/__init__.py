"""Window focus, z-order, and error dialogs."""

from joypad.platform.windows.hwnd.dialog import show_error_message
from joypad.platform.windows.hwnd.foreground import (
    bring_any_other_window_to_foreground as _bring_any_other_window_to_foreground,
)
from joypad.platform.windows.hwnd.foreground import (
    bring_game_to_foreground,
    bring_process_window_to_foreground,
)
from joypad.platform.windows.hwnd.foreground import (
    bring_launcher_to_front as _bring_launcher_to_front,
)
from joypad.platform.windows.hwnd.timed_pump import timed_pump as _sleep_with_spinner
from joypad.platform.windows.hwnd.zorder import resize_launcher_window, send_launcher_to_back

__all__ = [
    "_bring_any_other_window_to_foreground",
    "_bring_launcher_to_front",
    "_sleep_with_spinner",
    "bring_game_to_foreground",
    "bring_process_window_to_foreground",
    "resize_launcher_window",
    "send_launcher_to_back",
    "show_error_message",
]
