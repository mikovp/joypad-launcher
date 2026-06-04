from joypad.bootstrap import _build_game_row_numbers
from joypad.platform.windows import find_exe_in_uninstall_registry


def test_build_game_row_numbers_resets_per_section():
    list_items = [
        {"kind": "header"},
        {"kind": "game"},
        {"kind": "game"},
        {"kind": "header"},
        {"kind": "game"},
    ]
    assert _build_game_row_numbers(list_items) == {1: 1, 2: 2, 4: 1}


def test_find_exe_in_uninstall_registry_non_windows():
    import sys

    if sys.platform == "win32":
        return
    assert find_exe_in_uninstall_registry("twitch", exe_basename="Twitch.exe") is None
