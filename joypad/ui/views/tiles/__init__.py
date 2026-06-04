"""Tile-view rendering and navigation for the launcher."""

from joypad.ui.views.tiles.drawing import draw_tiles_view
from joypad.ui.views.tiles.geometry import (
    compute_tile_grid,
    rebuild_tile_geometry,
    rebuild_tile_layout,
    tile_max_scroll_y,
    tile_row_stride,
)
from joypad.ui.views.tiles.navigation import (
    _section_header_y_for_pick,
    _tile_entry_for_pick,
    _tile_pick_location,
    _tile_snap_scroll,
    tile_move,
    tile_page_scroll,
    tile_section_jump,
    tile_selected_game,
)

__all__ = [
    "compute_tile_grid",
    "draw_tiles_view",
    "rebuild_tile_geometry",
    "rebuild_tile_layout",
    "tile_max_scroll_y",
    "tile_move",
    "tile_page_scroll",
    "tile_row_stride",
    "tile_section_jump",
    "tile_selected_game",
    "_section_header_y_for_pick",
    "_tile_entry_for_pick",
    "_tile_pick_location",
    "_tile_snap_scroll",
]
