"""Live settings application and font/layout reload."""

import pygame

from joypad.config.settings import _TILE_SCALE_DEFAULT
from joypad.config.theme import (
    parse_tile_scale,
    scale_theme_fonts_for_screen,
    theme_from_config,
    ui_mode_from_theme,
)
from joypad.ui.background import load_background_surface, resolve_background_image
from joypad.ui.overlay.menu.layout import rebuild_settings_layout
from joypad.ui.views import list as lst
from joypad.ui.views import tiles


def reload_fonts_and_layout(state):
    state.theme = theme_from_config(state.config)
    theme_section = state.config.get("theme") or {}
    state.ui_mode = ui_mode_from_theme(theme_section)
    state.tile_scale = parse_tile_scale(theme_section.get("tile_scale"), _TILE_SCALE_DEFAULT)
    state.bg_color = state.theme["background"]
    state.text_color = state.theme["text"]
    state.highlight_color = state.theme["cursor"]
    state.title_color = state.theme["title"]
    state.font_bold_title = state.theme["font_bold_title"]
    state.font_bold_list = state.theme["font_bold_list"]
    scale_theme_fonts_for_screen(state.theme, state.config.get("theme") or {}, state.h)
    state.font_size_title = state.theme["font_size_title"]
    state.font_size_list = state.theme["font_size_list"]
    font_size_hint_cfg = state.theme.get("font_size_hint")
    state.font_size_hint = (
        font_size_hint_cfg if font_size_hint_cfg is not None else max(10, state.font_size_title // 2)
    )
    state.font_title = pygame.font.SysFont("Segoe UI", state.font_size_title, bold=state.font_bold_title)
    state.font_list = pygame.font.SysFont("Segoe UI", state.font_size_list, bold=state.font_bold_list)
    state.font_category = pygame.font.SysFont("Segoe UI", state.font_size_list, bold=True)
    state.font_hint = pygame.font.SysFont("Segoe UI", state.font_size_hint, bold=state.font_bold_title)
    state.line_h = max(36, int(state.font_size_list * 2))
    state.hint_line_h = state.font_hint.get_linesize()
    state.list_start_y = 36 + state.hint_line_h * 2
    state.list_bottom_margin = max(44, state.hint_line_h + 24)
    state.list_line_skip = state.font_list.get_linesize() + 3
    state.title_surface, state.hint_surface = lst._hint_surfaces(state)
    tiles.rebuild_tile_geometry(state)
    state.cum_starts, state.row_specs, state.list_content_height = lst.build_list_layout(state)
    state.viewport_h = max(60, state.h - state.list_start_y - state.list_bottom_margin)
    state.max_scroll_y = max(0, state.list_content_height - state.viewport_h)


def apply_setting_live(state, key):
    if key == "background":
        state.background_image_path = resolve_background_image(state.config)
        state.bg_surface = load_background_surface(state.background_image_path, state.w, state.h)
    elif key in (
        "ui_mode",
        "tile_scale",
        "font_scale", "font_size_title", "font_size_list", "font_size_hint",
        "font_bold_title", "font_bold_list", "auto_font_boost",
    ):
        reload_fonts_and_layout(state)
    elif key == "cdn_covers":
        _theme_cfg = state.config.get("theme") or {}
        state.cover_cache._cdn.enabled = bool(_theme_cfg.get("cdn_covers", True))
        if state.cover_cache._cdn.enabled:
            state.cover_cache.prefetch_async(state.games)
    elif key == "steam_silent":
        state.steam_start_args = (state.config.get("steam_start_args") or "").strip() or None
    rebuild_settings_layout(state)
