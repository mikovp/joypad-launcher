"""Settings / system-overlay cluster extracted from run_launcher.

Behavior-preserving 1:1 move of the overlay nested functions. Each function
takes the shared AppState `state` as its first parameter. Cross-calls to the
tile/list view clusters are routed through their modules; sibling overlay
functions are called module-internally; the two run_launcher orchestration
callables (`try_launch_game`, `stop_active_remap`) are injected on `state`.
"""

import math
import time

import pygame

from joypad.config.loader import save_config
from joypad.config.settings import (
    _TILE_SCALE_DEFAULT,
    apply_setting_toggle,
    build_settings_menu,
)
from joypad.config.theme import (
    parse_tile_scale,
    scale_theme_fonts_for_screen,
    theme_from_config,
    ui_mode_from_theme,
)
from joypad.launch.launcher import perform_system_action
from joypad.paths import _BASE_DIR
from joypad.ui.background import load_background_surface, resolve_background_image
from joypad.ui.views import list as lst
from joypad.ui.views import tiles


def _settings_first_row(state):
    for i, it in enumerate(state.settings_menu_items):
        if it.get("kind") in ("setting", "action"):
            return i
    return 0


def rebuild_settings_layout(state):
    state.settings_menu_items = build_settings_menu(state.config)
    cat_skip = state.font_category.get_linesize() + 8
    setting_h = state.font_list.get_linesize() + 8
    state.settings_cum_starts = []
    state.settings_row_specs = []
    y_acc = 0
    for item in state.settings_menu_items:
        state.settings_cum_starts.append(y_acc)
        if item.get("kind") == "header":
            h_row = cat_skip
            state.settings_row_specs.append({"kind": "header", "height": h_row, "title": item["title"]})
        else:
            h_row = setting_h
            state.settings_row_specs.append({"kind": "row", "height": h_row, "item": item})
        y_acc += h_row
    state.settings_content_h = y_acc


def overlay_items(state):
    return state.settings_menu_items if state.overlay_menu == "settings" else state.system_menu_items


def _overlay_snap_scroll(state):
    if state.overlay_menu != "settings" or not state.settings_row_specs:
        return
    header_h = 48
    max_menu_h = max(120, state.h - 80)
    body_h = max_menu_h - header_h
    max_scroll = max(0, state.settings_content_h - body_h)
    sel_top = state.settings_cum_starts[state.overlay_index]
    sel_h = state.settings_row_specs[state.overlay_index]["height"]
    sel_bot = sel_top + sel_h
    if sel_top < state.overlay_scroll_y:
        state.overlay_scroll_y = sel_top
    elif sel_bot > state.overlay_scroll_y + body_h:
        state.overlay_scroll_y = sel_bot - body_h
    state.overlay_scroll_y = max(0, min(state.overlay_scroll_y, max_scroll))


def overlay_move(state, delta):
    if state.overlay_menu == "settings":
        n = len(state.settings_menu_items)
        if n == 0:
            return
        for _ in range(n):
            state.overlay_index = (state.overlay_index + delta) % n
            if state.settings_menu_items[state.overlay_index].get("kind") in ("setting", "action"):
                break
        _overlay_snap_scroll(state)
        return
    items = overlay_items(state)
    state.overlay_index = (state.overlay_index + delta) % len(items)
    menu_line_h = state.font_list.get_linesize() + 8
    header_h = 48
    max_menu_h = max(120, state.h - 80)
    body_h = max_menu_h - header_h
    max_scroll = max(0, len(items) * menu_line_h - body_h)
    row_top = state.overlay_index * menu_line_h
    row_bot = row_top + menu_line_h
    if row_top < state.overlay_scroll_y:
        state.overlay_scroll_y = row_top
    elif row_bot > state.overlay_scroll_y + body_h:
        state.overlay_scroll_y = min(max_scroll, row_bot - body_h)
    state.overlay_scroll_y = max(0, min(state.overlay_scroll_y, max_scroll))


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


def overlay_back(state):
    if state.overlay_menu == "settings":
        state.overlay_menu = "system"
        state.overlay_index = 0
    else:
        state.overlay_menu = None
        state.overlay_index = 0


def overlay_confirm(state):
    if state.overlay_menu == "system":
        item = state.system_menu_items[state.overlay_index]
        key = item["key"]
        if key == "resume":
            state.overlay_menu = None
            state.overlay_index = 0
        elif key == "settings":
            state.overlay_menu = "settings"
            state.overlay_index = _settings_first_row(state)
            state.overlay_scroll_y = 0
            rebuild_settings_layout(state)
        elif key == "input_remap_open":
            from joypad.ui.editor import InputRemapSession

            state.overlay_menu = None
            state.overlay_index = 0
            state.input_remap_session = InputRemapSession(
                state.screen,
                (state.font_title, state.font_list, state.font_hint),
                (state.bg_color, state.text_color, state.highlight_color, state.title_color),
                state.config,
                state.games,
                _BASE_DIR,
                save_config,
            )
        elif key == "exit":
            state.running = False
        elif key == "shutdown":
            perform_system_action("shutdown")
            state.running = False
        elif key == "reboot":
            perform_system_action("reboot")
            state.running = False
    elif state.overlay_menu == "settings":
        item = state.settings_menu_items[state.overlay_index]
        if item.get("kind") == "header":
            return
        key = item.get("key")
        if key == "back":
            overlay_back(state)
        elif key == "input_remap_open":
            from joypad.ui.editor import InputRemapSession

            state.overlay_menu = None
            state.overlay_index = 0
            state.input_remap_session = InputRemapSession(
                state.screen,
                (state.font_title, state.font_list, state.font_hint),
                (state.bg_color, state.text_color, state.highlight_color, state.title_color),
                state.config,
                state.games,
                _BASE_DIR,
                save_config,
            )
        elif apply_setting_toggle(state.config, key):
            apply_setting_live(state, key)


_LAUNCH_SPINNER_INTRO_FRAMES = 36
_LAUNCH_SPINNER_FRAME_DELAY = 0.1


def capture_launching_snapshot(state):
    """Frozen launcher frame for the launching spinner overlay."""
    return state.screen.copy()


def draw_launching_spinner_frame(state, saved, frame_i):
    """One spinner frame on top of the saved launcher snapshot."""
    blur_scale = 5
    dim_alpha = 140
    dot_count = 12
    r_max, r_min = 7, 1
    orbit_radius = 26
    dim_color = tuple(max(0, min(255, int(c * 0.2))) for c in state.text_color)
    small = pygame.transform.smoothscale(saved, (max(1, state.w // blur_scale), max(1, state.h // blur_scale)))
    blurred = pygame.transform.smoothscale(small, (state.w, state.h))
    state.screen.blit(blurred, (0, 0))
    dim = pygame.Surface((state.w, state.h))
    dim.set_alpha(dim_alpha)
    dim.fill((0, 0, 0))
    state.screen.blit(dim, (0, 0))
    phase = (frame_i % dot_count)
    cx, cy = state.w // 2, state.h // 2
    for j in range(dot_count):
        raw = (phase - j) % dot_count
        dist = raw if raw <= dot_count / 2 else dot_count - raw
        if raw > dot_count / 2:
            dist = 999
        t = min(1.0, dist / 6.0)
        radius = max(r_min, r_max - t * (r_max - r_min))
        t_soft = t * t
        brightness = max(0.0, 1.0 - t_soft * 1.1)
        color = tuple(
            max(0, min(255, int(dim_color[c] + (state.text_color[c] - dim_color[c]) * brightness)))
            for c in range(3)
        )
        angle = math.radians(j * (360 / dot_count) - 90)
        x = cx + orbit_radius * math.cos(angle)
        y = cy + orbit_radius * math.sin(angle)
        pygame.draw.circle(state.screen, color, (int(x), int(y)), max(1, int(radius)))


def tick_launching_spinner(state, saved, frame_i, *, sleep=False, frame_delay=_LAUNCH_SPINNER_FRAME_DELAY):
    """Advance and show one spinner frame; returns next frame index."""
    draw_launching_spinner_frame(state, saved, frame_i)
    pygame.display.flip()
    pygame.event.pump()
    if sleep:
        time.sleep(frame_delay)
    return frame_i + 1


def begin_launching_overlay(state, _game_name=None, intro_frames=_LAUNCH_SPINNER_INTRO_FRAMES):
    """Capture screen and run intro spinner; returns (snapshot, next_frame) for continued ticks."""
    saved = capture_launching_snapshot(state)
    frame = 0
    for _ in range(intro_frames):
        frame = tick_launching_spinner(state, saved, frame, sleep=True)
    return saved, frame


def show_launching_overlay(state, _game_name=None):
    """Blurred overlay with rotating dots (intro only; use tick_launching_spinner while waiting)."""
    begin_launching_overlay(state, _game_name)
