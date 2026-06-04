"""Tests for editor input navigation."""

from joypad.ui.editor import input as editor_input


class _FakeSession:
    def __init__(self):
        self.mode = "game_list"
        self.remapped = [{"name": "A"}, {"name": "B"}]
        self.game_index = 0
        self.pick_candidates = []
        self.pick_index = 0
        self.slots = []
        self.slot_index = 0
        self.finished = False
        self._snap_grid_scroll = lambda areas=None: None


def test_nav_game_list_wraps():
    s = _FakeSession()
    editor_input.nav(s, 1)
    assert s.game_index == 1
    editor_input.nav(s, 1)
    assert s.game_index == 0


def test_back_from_pick_game_returns_to_list():
    s = _FakeSession()
    s.mode = "pick_game"
    editor_input.back(s)
    assert s.mode == "game_list"
    assert s.finished is False


def test_back_from_game_list_finishes():
    s = _FakeSession()
    editor_input.back(s)
    assert s.finished is True
