# tests/test_home_integration.py
import types
import joypad.ui.views.list.dispatch as disp


def _home_state():
    shelves = [
        {"title": "Steam", "games": [{"name": "Hades"}, {"name": "Celeste"}]},
        {"title": "All", "games": [{"name": "Celeste"}, {"name": "Hades"}]},
    ]
    from joypad.ui.views.home.navigation import home_init_focus
    st = types.SimpleNamespace(ui_mode="home", home_shelves=shelves, home_focus=None)
    home_init_focus(st)
    return st


def test_dispatch_routes_to_home():
    s = _home_state()
    disp.nav_horizontal(s, 1)
    assert s.home_focus["col"] == 1
    disp.nav_vertical(s, -1)
    assert s.home_focus["zone"] == "hero"


def test_get_selected_item_home():
    s = _home_state()
    item = disp.get_selected_item(s)
    assert item == {"kind": "game", "game": {"name": "Hades"}}


def test_nav_lb_rb_home_moves_shelf():
    s = _home_state()
    disp.nav_lb_rb(s, 1)
    assert s.home_focus["shelf"] == 1
