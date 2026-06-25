"""Unified navigation dispatch (list vs tiles vs home)."""

from joypad.ui.views import home, tiles
from joypad.ui.views.list.navigation import move_game_selection, page_scroll


def get_selected_item(state):
    if state.ui_mode == "home":
        g = home.home_selected_game(state)
        return {"kind": "game", "game": g} if g is not None else None
    if state.ui_mode == "tiles":
        g = tiles.tile_selected_game(state)
        return {"kind": "game", "game": g} if g is not None else None
    if 0 <= state.selected < len(state.list_items) and state.list_items[state.selected]["kind"] == "game":
        return state.list_items[state.selected]
    return None


def nav_vertical(state, delta):
    if state.ui_mode == "home":
        home.home_move(state, 0, delta)
    elif state.ui_mode == "tiles":
        tiles.tile_move(state, 0, delta)
    else:
        move_game_selection(state, delta)


def nav_horizontal(state, delta):
    if state.ui_mode == "home":
        home.home_move(state, delta, 0)
    elif state.ui_mode == "tiles":
        tiles.tile_move(state, delta, 0)


def nav_page(state, delta):
    if state.ui_mode == "home":
        home.home_lb_rb(state, delta)
    elif state.ui_mode == "tiles":
        tiles.tile_page_scroll(state, delta)
    else:
        page_scroll(state, delta)


def nav_lb_rb(state, delta):
    if state.ui_mode == "home":
        home.home_lb_rb(state, delta)
    elif state.ui_mode == "tiles":
        _sec_i, local = tiles._tile_pick_location(state, state.tile_pick)
        if local == 0:
            tiles.tile_section_jump(state, delta)
        else:
            tiles.tile_page_scroll(state, delta)
    else:
        page_scroll(state, delta)
