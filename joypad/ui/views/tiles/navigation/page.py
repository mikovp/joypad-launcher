"""Tile page scroll and section jump."""

from joypad.ui.views.tiles.geometry import tile_max_scroll_y, tile_row_stride
from joypad.ui.views.tiles.navigation.pick import global_pick, section_header_y_for_pick, tile_pick_location
from joypad.ui.views.tiles.navigation.scroll import tile_snap_scroll


def tile_page_scroll(state, delta_pages):
    if delta_pages == 0:
        return
    step = max(state.tile_geom["grid_h"] // 2, tile_row_stride(state) * 2)
    state.tile_scroll_y = max(
        0,
        min(tile_max_scroll_y(state), state.tile_scroll_y + delta_pages * step),
    )
    state.tile_snap_scroll = False


def tile_section_jump(state, delta):
    if not state.tile_sections or delta == 0:
        return
    sec_i, _local = tile_pick_location(state, state.tile_pick)
    nsec = len(state.tile_sections)
    for _ in range(nsec):
        sec_i = (sec_i + delta) % nsec
        if state.tile_sections[sec_i]["games"]:
            break
    state.tile_pick = global_pick(state, sec_i, 0)
    state.tile_scroll_y = section_header_y_for_pick(state, state.tile_pick)
    state.tile_snap_scroll = True
    tile_snap_scroll(state)
