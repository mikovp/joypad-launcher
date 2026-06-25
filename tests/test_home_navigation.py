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


def test_left_at_col0_enters_rail():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)
    assert s.home_focus["zone"] == "rail"


def test_right_within_shelf_then_left_back():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, 1, 0)
    assert s.home_focus["col"] == 1 and s.home_focus["zone"] == "shelf"
    nav.home_move(s, -1, 0)
    assert s.home_focus["col"] == 0 and s.home_focus["zone"] == "shelf"


def test_up_from_first_shelf_to_hero_and_back():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, 0, -1)
    assert s.home_focus["zone"] == "hero"
    nav.home_move(s, 0, 1)
    assert s.home_focus["zone"] == "shelf" and s.home_focus["shelf"] == 0


def test_down_clamps_col_to_new_shelf():
    s = _state([
        {"title": "A", "games": [{"name": "a"}, {"name": "b"}, {"name": "c"}]},
        {"title": "B", "games": [{"name": "x"}]},
    ])
    nav.home_init_focus(s)
    nav.home_move(s, 1, 0); nav.home_move(s, 1, 0)   # col=2
    nav.home_move(s, 0, 1)                            # down to shelf B (len 1)
    assert s.home_focus["shelf"] == 1 and s.home_focus["col"] == 0


def test_rail_right_returns_to_content():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)                # into rail
    nav.home_move(s, 0, 1)                 # move rail index down
    assert s.home_focus["rail"] == 1
    nav.home_move(s, 1, 0)                 # right -> back to content
    assert s.home_focus["zone"] == "shelf"


def test_lb_rb_moves_shelf():
    s = _state(_shelves()); nav.home_init_focus(s)
    nav.home_lb_rb(s, 1)
    assert s.home_focus["shelf"] == 1
    nav.home_lb_rb(s, -1)
    assert s.home_focus["shelf"] == 0


def _state_full(shelves):
    return types.SimpleNamespace(
        home_shelves=shelves, home_focus=None, overlay_menu=None, overlay_index=None
    )


def test_confirm_on_game_calls_launch():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    calls = []
    assert nav.home_confirm(s, lambda: calls.append(1) or True) is True
    assert calls == [1]


def test_confirm_rail_settings_opens_settings():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)                 # into rail (index 0 = home)
    nav.home_move(s, 0, 1)                  # index 1 = settings
    assert nav.home_confirm(s, lambda: True) is False
    assert s.overlay_menu == "settings" and s.overlay_index == 0


def test_confirm_rail_power_opens_system():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)
    nav.home_move(s, 0, 1); nav.home_move(s, 0, 1)   # index 2 = power
    assert nav.home_confirm(s, lambda: True) is False
    assert s.overlay_menu == "system"


def test_confirm_rail_home_focuses_content():
    s = _state_full(_shelves()); nav.home_init_focus(s)
    nav.home_move(s, -1, 0)                 # rail index 0 = home
    assert nav.home_confirm(s, lambda: True) is False
    assert s.home_focus["zone"] == "shelf"
