"""List-view rendering and navigation for the launcher."""

from joypad.ui.views.list.dispatch import (
    get_selected_item,
    nav_horizontal,
    nav_lb_rb,
    nav_page,
    nav_vertical,
)
from joypad.ui.views.list.drawing import _hint_surfaces, draw_list_view, footer_line_count
from joypad.ui.views.list.layout import build_list_layout
from joypad.ui.views.list.navigation import (
    _first_game_row_index,
    move_game_selection,
    move_selection_by_viewport,
    page_scroll,
    snap_list_scroll,
)

__all__ = [
    "_first_game_row_index",
    "_hint_surfaces",
    "footer_line_count",
    "build_list_layout",
    "draw_list_view",
    "get_selected_item",
    "move_game_selection",
    "move_selection_by_viewport",
    "nav_horizontal",
    "nav_lb_rb",
    "nav_page",
    "nav_vertical",
    "page_scroll",
    "snap_list_scroll",
]
