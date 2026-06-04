"""Mutable session state for the launcher game loop (run_launcher)."""

from dataclasses import dataclass
from typing import Any


@dataclass
class AppState:
    # All fields are assigned during run_launcher initialization before first
    # read; defaults are placeholders. Names match the former closure locals.
    selected: Any = None
    list_snap_scroll_to_selection: Any = None
    tile_geom: Any = None
    tile_scale: Any = None
    tile_layout: Any = None
    tile_all_games: Any = None
    tile_content_h: Any = None
    tile_scroll_y: Any = None
    tile_pick: Any = None
    tile_snap_scroll: Any = None
    settings_menu_items: Any = None
    settings_cum_starts: Any = None
    settings_row_specs: Any = None
    settings_content_h: Any = None
    overlay_scroll_y: Any = None
    overlay_index: Any = None
    overlay_menu: Any = None
    theme: Any = None
    bg_color: Any = None
    text_color: Any = None
    highlight_color: Any = None
    title_color: Any = None
    font_size_title: Any = None
    font_size_list: Any = None
    font_size_hint: Any = None
    font_bold_title: Any = None
    font_bold_list: Any = None
    font_title: Any = None
    font_list: Any = None
    font_category: Any = None
    font_hint: Any = None
    hint_line_h: Any = None
    list_start_y: Any = None
    list_bottom_margin: Any = None
    list_line_skip: Any = None
    title_surface: Any = None
    hint_surface: Any = None
    ui_mode: Any = None
    cum_starts: Any = None
    row_specs: Any = None
    list_content_height: Any = None
    viewport_h: Any = None
    max_scroll_y: Any = None
    bg_surface: Any = None
    background_image_path: Any = None
    steam_start_args: Any = None
    running: Any = None
    input_remap_session: Any = None
    # Read-only session data carried for the tile-view cluster (joypad.ui.views.tiles).
    config: Any = None
    cover_cache: Any = None
    w: Any = None
    h: Any = None
    screen: Any = None
    tile_sections: Any = None
    # Read-only session data carried for the list-view cluster (joypad.ui.views.list).
    list_items: Any = None
    game_row_numbers: Any = None
    margin_right: Any = None
    list_left: Any = None
    # Read-only session data carried for the overlay cluster (joypad.ui.overlay).
    system_menu_items: Any = None
    games: Any = None
