"""Tile view scroll snapping."""

from joypad.ui.views.tiles.geometry import tile_max_scroll_y, tile_row_stride
from joypad.ui.views.tiles.navigation.pick import section_header_y_for_pick, tile_entry_for_pick


def tile_snap_scroll(state):
    ent = tile_entry_for_pick(state, state.tile_pick)
    if not ent:
        return
    header_y = section_header_y_for_pick(state, state.tile_pick)
    top = ent["y"]
    bot = top + ent["h"] + state.font_hint.get_linesize() + 8
    view = state.tile_geom["grid_h"]
    stride = max(1, tile_row_stride(state))
    rows_from_header = (top - header_y) // stride if top > header_y else 0
    if top < state.tile_scroll_y:
        if rows_from_header <= 1:
            state.tile_scroll_y = header_y
        else:
            state.tile_scroll_y = top
    elif bot > state.tile_scroll_y + view:
        state.tile_scroll_y = bot - view
    state.tile_scroll_y = max(0, min(state.tile_scroll_y, tile_max_scroll_y(state)))
