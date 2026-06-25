"""Mutable session state for the launcher game loop (run_launcher)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AppState:
    # All fields are assigned during run_launcher initialization before first
    # read; the None defaults are placeholders. Names match the former closure
    # locals. pygame objects (Font/Surface) and external handles are typed Any
    # (no type stubs available).

    # --- list-view selection / scrolling ---
    selected: int | None = None
    list_snap_scroll_to_selection: bool | None = None
    cum_starts: list | None = None
    row_specs: list | None = None
    list_content_height: int | None = None
    viewport_h: int | None = None
    max_scroll_y: int | None = None
    list_scroll_y: int | None = None

    # --- tile-view geometry / selection ---
    tile_geom: dict | None = None
    tile_scale: float | None = None
    tile_layout: list | None = None
    tile_all_games: list | None = None
    tile_content_h: int | None = None
    tile_scroll_y: int | None = None
    tile_pick: int | None = None
    tile_snap_scroll: bool | None = None

    # --- home-view geometry / focus ---
    home_geom: dict | None = None
    home_shelves: list | None = None
    home_focus: dict | None = None

    # --- settings / overlay ---
    settings_menu_items: list | None = None
    settings_cum_starts: list | None = None
    settings_row_specs: list | None = None
    settings_content_h: int | None = None
    overlay_scroll_y: int | None = None
    overlay_index: int | None = None
    overlay_menu: str | None = None  # None | "system" | "settings"

    # --- theme colors / fonts ---
    theme: dict | None = None
    bg_color: tuple | None = None
    text_color: tuple | None = None
    highlight_color: tuple | None = None
    title_color: tuple | None = None
    font_size_title: int | None = None
    font_size_list: int | None = None
    font_size_hint: int | None = None
    font_bold_title: bool | None = None
    font_bold_list: bool | None = None
    font_title: Any = None       # pygame.font.Font
    font_list: Any = None        # pygame.font.Font
    font_category: Any = None     # pygame.font.Font
    font_hint: Any = None        # pygame.font.Font
    hint_line_h: int | None = None
    list_start_y: int | None = None
    list_bottom_margin: int | None = None
    list_line_skip: int | None = None
    title_surface: Any = None    # pygame.Surface
    hint_surface: Any = None     # pygame.Surface
    ui_mode: str | None = None

    # --- background / window / session ---
    bg_surface: Any = None       # pygame.Surface | None
    background_image_path: str | None = None
    steam_start_args: str | None = None
    running: bool | None = None
    input_remap_session: Any = None  # joypad.ui.editor.InputRemapSession | None

    steam_active_login: str | None = None
    footer_lines: int | None = None

    # Read-only session data carried for the tile-view cluster (joypad.ui.views.tiles).
    config: dict | None = None
    cover_cache: Any = None      # joypad.covers.cache.CoverCache
    w: int | None = None
    h: int | None = None
    screen: Any = None           # pygame.Surface
    tile_sections: list | None = None

    # Read-only session data carried for the list-view cluster (joypad.ui.views.list).
    list_items: list | None = None
    game_row_numbers: dict | None = None
    margin_right: int | None = None
    list_left: int | None = None

    # Read-only session data carried for the overlay cluster (joypad.ui.overlay).
    system_menu_items: list | None = None
    games: list | None = None
