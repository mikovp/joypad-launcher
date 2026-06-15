"""Pygame display, fonts, and cover cache initialization."""

from __future__ import annotations

import sys
from typing import Any

import pygame

from joypad.app_state import AppState
from joypad.config.settings import _TILE_SCALE_DEFAULT
from joypad.config.theme import parse_tile_scale, scale_theme_fonts_for_screen
from joypad.paths import _BASE_DIR
from joypad.platform.windows import resize_launcher_window
from joypad.ui.background import load_background_surface
from joypad.ui.views import list as lst
from joypad.ui.views import tiles
from joypad.ui.views.tiles import compute_tile_grid


def build_cover_cache(config: dict, games: list, steam_dir: str | None):
    from joypad.covers.cache import CoverCache

    theme_cfg = config.get("theme") or {}
    covers_folder = (theme_cfg.get("covers_folder") or "covers").strip() or "covers"
    cdn_covers = theme_cfg.get("cdn_covers")
    if cdn_covers is None:
        cdn_covers = True
    else:
        cdn_covers = bool(cdn_covers)
    cdn_cache_folder = (theme_cfg.get("cdn_cache_folder") or "cover_cdn_cache").strip() or "cover_cdn_cache"
    rawg_api_key = (config.get("rawg_api_key") or theme_cfg.get("rawg_api_key") or "").strip() or None
    cover_cache = CoverCache(
        _BASE_DIR,
        steam_dir=steam_dir,
        covers_subdir=covers_folder,
        cdn_enabled=cdn_covers,
        cdn_cache_subdir=cdn_cache_folder,
        rawg_api_key=rawg_api_key,
    )
    cover_cache.prefetch_async(games)
    return cover_cache


def init_pygame_display(state: AppState, config: dict) -> Any:
    pygame.init()
    pygame.joystick.init()

    info = pygame.display.Info()
    w, h = info.current_w, info.current_h
    state.w = w
    state.h = h
    scale_theme_fonts_for_screen(state.theme, config.get("theme") or {}, h)
    state.font_size_title = state.theme["font_size_title"]
    state.font_size_list = state.theme["font_size_list"]
    font_size_hint_cfg = state.theme.get("font_size_hint")
    state.font_size_hint = (
        font_size_hint_cfg if font_size_hint_cfg is not None else max(10, state.font_size_title // 2)
    )
    screen = pygame.display.set_mode((w, h), pygame.NOFRAME)
    state.screen = screen
    pygame.display.set_caption("Joypad Launcher")
    pygame.mouse.set_visible(False)

    state.bg_surface = load_background_surface(state.background_image_path, w, h)
    hwnd = pygame.display.get_wm_info().get("window") if sys.platform == "win32" else None
    resize_launcher_window(hwnd, w, h)
    return hwnd


def apply_footer_layout(state: AppState) -> None:
    state.footer_lines = lst.footer_line_count(state)
    state.list_bottom_margin = max(44, state.hint_line_h * state.footer_lines + 24)


def init_fonts_and_layouts(state: AppState, config: dict) -> None:
    h = state.h
    state.font_title = pygame.font.SysFont("Segoe UI", state.font_size_title, bold=state.font_bold_title)
    state.font_list = pygame.font.SysFont("Segoe UI", state.font_size_list, bold=state.font_bold_list)
    state.font_category = pygame.font.SysFont("Segoe UI", state.font_size_list, bold=True)
    state.font_hint = pygame.font.SysFont("Segoe UI", state.font_size_hint, bold=state.font_bold_title)

    state.hint_line_h = state.font_hint.get_linesize()
    apply_footer_layout(state)
    state.list_start_y = 36 + state.hint_line_h * 2
    state.list_line_skip = state.font_list.get_linesize() + 3
    state.margin_right = 52
    state.list_left = 80

    state.cum_starts, state.row_specs, state.list_content_height = lst.build_list_layout(state)
    state.viewport_h = max(60, h - state.list_start_y - state.list_bottom_margin)
    state.max_scroll_y = max(0, state.list_content_height - state.viewport_h)
    state.list_scroll_y = 0
    state.list_snap_scroll_to_selection = True

    state.selected = lst._first_game_row_index(state)
    state.tile_pick = 0
    state.tile_scroll_y = 0
    theme_for_tiles = config.get("theme") or {}
    state.tile_scale = parse_tile_scale(theme_for_tiles.get("tile_scale"), _TILE_SCALE_DEFAULT)
    state.tile_geom = compute_tile_grid(
        state.w,
        h,
        state.hint_line_h,
        tile_scale=state.tile_scale,
        title_line_h=state.font_title.get_linesize(),
        footer_lines=state.footer_lines,
    )
    state.tile_layout = []
    state.tile_all_games = []
    state.tile_content_h = 0
    state.tile_snap_scroll = True
    tiles.rebuild_tile_layout(state)
