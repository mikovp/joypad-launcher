"""Application startup: load games, initialize pygame, populate AppState."""

from __future__ import annotations

import os
from dataclasses import dataclass

from joypad.app_state import AppState
from joypad.bootstrap.constants import SYSTEM_MENU_ITEMS
from joypad.bootstrap.display import build_cover_cache, init_fonts_and_layouts, init_pygame_display
from joypad.bootstrap.games import _build_game_row_numbers, collect_games
from joypad.config.loader import load_config
from joypad.config.theme import theme_from_config, ui_mode_from_theme
from joypad.games.model import build_categorized_game_list, build_tile_sections
from joypad.launch.session import LaunchSession
from joypad.paths import _BASE_DIR
from joypad.integrations.steam import active_steam_login, get_active_steam_account
from joypad.platform.windows import get_steam_path
from joypad.ui import overlay as ovl
from joypad.ui.background import resolve_background_image
from joypad.ui.views import list as lst


@dataclass
class BootResult:
    state: AppState
    launch: LaunchSession


def bootstrap() -> BootResult:
    """Load config, games, pygame, and UI state. Returns session ready for the main loop."""
    from ddcci import apply_startup_from_config, schedule_delayed_power_off

    state = AppState()
    config = load_config()
    state.config = config

    apply_startup_from_config(config, _BASE_DIR)
    games = collect_games(config)

    steam_path = get_steam_path(config)
    steam_dir = os.path.normpath(os.path.dirname(steam_path)) if steam_path else None
    active = get_active_steam_account(steam_dir) if steam_dir else None
    steam_active_login = active_steam_login(active)

    list_items = build_categorized_game_list(games, steam_active_login)
    state.list_items = list_items
    state.tile_sections = build_tile_sections(games, steam_active_login)
    state.game_row_numbers = _build_game_row_numbers(list_items)
    state.steam_active_login = steam_active_login

    state.cover_cache = build_cover_cache(config, games, steam_dir)

    theme_cfg = config.get("theme") or {}
    state.ui_mode = ui_mode_from_theme(theme_cfg)
    default_args = config.get("fullscreen_args", {})
    state.steam_start_args = (config.get("steam_start_args") or "").strip() or None
    steam_skip_restore_ids = {str(x) for x in (config.get("steam_skip_restore_ids") or [])}
    state.theme = theme_from_config(config)
    state.bg_color = state.theme["background"]
    state.text_color = state.theme["text"]
    state.highlight_color = state.theme["cursor"]
    state.title_color = state.theme["title"]
    state.font_bold_title = state.theme["font_bold_title"]
    state.font_bold_list = state.theme["font_bold_list"]
    state.background_image_path = resolve_background_image(config)

    hwnd = init_pygame_display(state, config)
    schedule_delayed_power_off(config, _BASE_DIR)
    init_fonts_and_layouts(state, config)

    state.system_menu_items = SYSTEM_MENU_ITEMS
    state.games = games
    state.settings_menu_items = []
    state.settings_cum_starts = []
    state.settings_row_specs = []
    state.settings_content_h = 0
    state.overlay_menu = None
    state.overlay_index = 0
    state.overlay_scroll_y = 0
    state.input_remap_session = None
    state.running = True

    ovl.rebuild_settings_layout(state)
    state.title_surface, state.hint_surface = lst._hint_surfaces(state)

    active_remap_proc = [None]
    launch = LaunchSession(
        steam_path=steam_path,
        default_args=default_args,
        steam_skip_restore_ids=steam_skip_restore_ids,
        hwnd=hwnd,
        active_remap_proc=active_remap_proc,
    )
    return BootResult(state=state, launch=launch)


__all__ = ["BootResult", "SYSTEM_MENU_ITEMS", "_build_game_row_numbers", "bootstrap", "collect_games"]
