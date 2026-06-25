import types
from joypad.ui.views.home import navigation as nav


def _state(shelves):
    return types.SimpleNamespace(home_shelves=shelves, home_focus=None)


def _shelves():
    return [
        {"title": "Steam", "games": [{"name": "Hades"}, {"name": "Celeste"}]},
        {"title": "All", "games": [{"name": "Celeste"}, {"name": "Hades"}]},
    ]


def test_init_focus_first_tile():
    s = _state(_shelves())
    nav.home_init_focus(s)
    assert s.home_focus["zone"] == "shelf"
    assert s.home_focus["shelf"] == 0 and s.home_focus["col"] == 0


def test_init_focus_empty_goes_rail():
    s = _state([])
    nav.home_init_focus(s)
    assert s.home_focus["zone"] == "rail"


def test_selected_game_tracks_focus():
    s = _state(_shelves())
    nav.home_init_focus(s)
    assert nav.home_selected_game(s)["name"] == "Hades"
    s.home_focus["zone"] = "rail"
    assert nav.home_selected_game(s) is None
