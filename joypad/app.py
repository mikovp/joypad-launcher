#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Joypad Launcher application entry point.
"""

import os
import sys

try:
    import pygame
except ImportError:
    print("Install pygame: pip install pygame")
    sys.exit(1)

from joypad.platform.windows import (
    get_steam_path,
    _send_launcher_to_back,
    _bring_process_window_to_foreground,
    _bring_game_to_foreground,
    _yield_for_game_window,
    _wait_for_game_and_restore,
    _show_error_message,
)

from joypad.paths import _BASE_DIR
from joypad.app_state import AppState
from joypad.ui.views import tiles
from joypad.ui.views import list as lst
from joypad.ui.views.tiles import compute_tile_grid
from joypad.ui import overlay as ovl

# Gamepad buttons (Xbox layout)
BTN_A = 0
BTN_B = 1
BTN_X = 2
BTN_Y = 3
BTN_LB = 4
BTN_RB = 5
BTN_BACK = 6
BTN_START = 7
AXIS_LEFT_Y = 1   # up negative, down positive
AXIS_LEFT_X = 0
DEADZONE = 0.5

from joypad.config.theme import (
    _theme_from_config, _scale_theme_fonts_for_screen,
    _ui_mode_from_theme, _parse_tile_scale,
)
from joypad.config.loader import load_config
from joypad.config.settings import (
    _TILE_SCALE_DEFAULT,
)
from joypad.games.model import (
    build_categorized_game_list, build_tile_sections,
)
from joypad.ui.background import resolve_background_image, _load_background_surface


from joypad.launch.launcher import (
    launch_steam_game, launch_epic_game, launch_nsp_game,
    perform_system_action,
)


def run():
    state = AppState()
    config = load_config()
    state.config = config
    from ddcci import apply_startup_from_config, schedule_delayed_power_off
    apply_startup_from_config(config, _BASE_DIR)
    if config.get("auto_scan"):
        from joypad.games.scan import scan_all
        steam_path = get_steam_path(config)
        if not steam_path:
            print("Steam not found. Specify steam_path in config.json (path to steam.exe).")
        games = scan_all(steam_path)
    else:
        games = config.get("games", [])

    nsp_roms_folder = (config.get("nsp_roms_folder") or "").strip()
    if nsp_roms_folder:
        from joypad.games.scan import scan_nsp_games
        games = list(games) + scan_nsp_games(nsp_roms_folder)

    if not games:
        print(
            "No games to show: Steam/Epic scan empty or disabled, config 'games' empty, "
            "and nsp_roms_folder missing or contains no .nsp files."
        )
        sys.exit(1)

    list_items = build_categorized_game_list(games)
    state.list_items = list_items
    tile_sections = build_tile_sections(games)
    state.tile_sections = tile_sections
    game_row_numbers = {}
    section_game_index = 0
    for _i, _it in enumerate(list_items):
        if _it["kind"] == "header":
            section_game_index = 0
        else:
            section_game_index += 1
            game_row_numbers[_i] = section_game_index
    state.game_row_numbers = game_row_numbers

    steam_path = get_steam_path(config)
    steam_dir = os.path.normpath(os.path.dirname(steam_path)) if steam_path else None
    from joypad.covers.cache import CoverCache

    _theme_cfg = config.get("theme") or {}
    covers_folder = (_theme_cfg.get("covers_folder") or "covers").strip() or "covers"
    cdn_covers = _theme_cfg.get("cdn_covers")
    if cdn_covers is None:
        cdn_covers = True
    else:
        cdn_covers = bool(cdn_covers)
    cdn_cache_folder = (_theme_cfg.get("cdn_cache_folder") or "cover_cdn_cache").strip() or "cover_cdn_cache"
    rawg_api_key = (config.get("rawg_api_key") or _theme_cfg.get("rawg_api_key") or "").strip() or None
    cover_cache = CoverCache(
        _BASE_DIR,
        steam_dir=steam_dir,
        covers_subdir=covers_folder,
        cdn_enabled=cdn_covers,
        cdn_cache_subdir=cdn_cache_folder,
        rawg_api_key=rawg_api_key,
    )
    cover_cache.prefetch_async(games)
    state.cover_cache = cover_cache
    state.ui_mode = _ui_mode_from_theme(_theme_cfg)
    default_args = config.get("fullscreen_args", {})
    state.steam_start_args = (config.get("steam_start_args") or "").strip() or None
    # Steam games that should not auto-restore launcher focus on exit (e.g. games with external launchers like Fallout 76).
    steam_skip_restore_ids = {
        str(x)
        for x in (config.get("steam_skip_restore_ids") or [])
    }
    state.theme = _theme_from_config(config)
    state.bg_color = state.theme["background"]
    state.text_color = state.theme["text"]
    state.highlight_color = state.theme["cursor"]
    state.title_color = state.theme["title"]
    state.font_bold_title = state.theme["font_bold_title"]
    state.font_bold_list = state.theme["font_bold_list"]
    state.background_image_path = resolve_background_image(config)

    pygame.init()
    pygame.joystick.init()

    info = pygame.display.Info()
    w, h = info.current_w, info.current_h
    state.w = w
    state.h = h
    _scale_theme_fonts_for_screen(state.theme, config.get("theme") or {}, h)
    state.font_size_title = state.theme["font_size_title"]
    state.font_size_list = state.theme["font_size_list"]
    font_size_hint_cfg = state.theme.get("font_size_hint")
    state.font_size_hint = (
        font_size_hint_cfg if font_size_hint_cfg is not None else max(10, state.font_size_title // 2)
    )
    # Borderless fullscreen window (non-exclusive fullscreen — better for streaming/Sunshine)
    screen = pygame.display.set_mode((w, h), pygame.NOFRAME)
    state.screen = screen
    pygame.display.set_caption("Joypad Launcher")
    pygame.mouse.set_visible(False)

    # Background image (path relative to launcher folder or absolute)
    state.bg_surface = _load_background_surface(state.background_image_path, w, h)
    hwnd = pygame.display.get_wm_info().get("window") if sys.platform == "win32" else None
    if hwnd and sys.platform == "win32":
        try:
            from ctypes import windll
            SWP_NOZORDER = 0x0004
            windll.user32.SetWindowPos(hwnd, None, 0, 0, w, h, SWP_NOZORDER)
        except Exception:
            pass

    schedule_delayed_power_off(config, _BASE_DIR)

    def rescan_joysticks():
        pygame.joystick.quit()
        pygame.joystick.init()
        js = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for j in js:
            j.init()
        pygame.event.clear()
        return js

    joysticks = rescan_joysticks()
    frames_since_rescan = 0
    RESCAN_INTERVAL = 120

    state.font_title = pygame.font.SysFont("Segoe UI", state.font_size_title, bold=state.font_bold_title)
    state.font_list = pygame.font.SysFont("Segoe UI", state.font_size_list, bold=state.font_bold_list)
    state.font_category = pygame.font.SysFont("Segoe UI", state.font_size_list, bold=True)
    state.font_hint = pygame.font.SysFont("Segoe UI", state.font_size_hint, bold=state.font_bold_title)

    state.line_h = max(36, int(state.font_size_list * 2))
    state.hint_line_h = state.font_hint.get_linesize()
    state.list_start_y = 36 + state.hint_line_h * 2
    state.list_bottom_margin = max(44, state.hint_line_h + 24)
    state.list_line_skip = state.font_list.get_linesize() + 3
    margin_right = 52
    state.margin_right = margin_right
    list_left = 80
    state.list_left = list_left

    def build_list_layout():
        return lst.build_list_layout(state)

    state.cum_starts, state.row_specs, state.list_content_height = build_list_layout()
    state.viewport_h = max(60, h - state.list_start_y - state.list_bottom_margin)
    state.max_scroll_y = max(0, state.list_content_height - state.viewport_h)
    scroll_y = 0
    state.list_snap_scroll_to_selection = True

    def move_selection_by_viewport(delta_pages):
        return lst.move_selection_by_viewport(state, delta_pages)

    def page_scroll(delta_pages):
        return lst.page_scroll(state, delta_pages)

    def _first_game_row_index():
        return lst._first_game_row_index(state)

    def move_game_selection(delta):
        return lst.move_game_selection(state, delta)

    state.selected = _first_game_row_index()
    state.tile_pick = 0
    state.tile_scroll_y = 0
    _theme_for_tiles = config.get("theme") or {}
    state.tile_scale = _parse_tile_scale(_theme_for_tiles.get("tile_scale"), _TILE_SCALE_DEFAULT)
    state.tile_geom = compute_tile_grid(
        w, h, state.hint_line_h, tile_scale=state.tile_scale, title_line_h=state.font_title.get_linesize()
    )
    state.tile_layout = []
    state.tile_all_games = []
    state.tile_content_h = 0
    state.tile_snap_scroll = True
    axis_held = 0  # pause between selection steps (lower = more responsive)
    AXIS_REPEAT_FRAMES = 18  # ~0.3s at 60 FPS — pause between selection steps

    def _hint_surfaces():
        return lst._hint_surfaces(state)

    def rebuild_tile_geometry():
        return tiles.rebuild_tile_geometry(state)

    def tile_row_stride():
        return tiles.tile_row_stride(state)

    def rebuild_tile_layout():
        return tiles.rebuild_tile_layout(state)

    rebuild_tile_layout()

    def tile_selected_game():
        return tiles.tile_selected_game(state)

    def _tile_pick_location(pick):
        return tiles._tile_pick_location(state, pick)

    def _global_pick(section_i, local_i):
        return tiles._global_pick(state, section_i, local_i)

    def _tile_entry_for_pick(pick):
        return tiles._tile_entry_for_pick(state, pick)

    def _section_header_y_for_pick(pick):
        return tiles._section_header_y_for_pick(state, pick)

    def tile_max_scroll_y():
        return tiles.tile_max_scroll_y(state)

    def _tile_snap_scroll():
        return tiles._tile_snap_scroll(state)

    def _tile_step_section(sec_i, delta, col):
        return tiles._tile_step_section(state, sec_i, delta, col)

    def _tile_below(local, row, col, cols, n, max_row):
        return tiles._tile_below(state, local, row, col, cols, n, max_row)

    def _tile_above(local, row, col, cols, n):
        return tiles._tile_above(state, local, row, col, cols, n)

    def tile_move(dx, dy):
        return tiles.tile_move(state, dx, dy)

    def tile_page_scroll(delta_pages):
        return tiles.tile_page_scroll(state, delta_pages)

    def tile_section_jump(delta):
        return tiles.tile_section_jump(state, delta)

    def get_selected_item():
        return lst.get_selected_item(state)

    def nav_vertical(delta):
        return lst.nav_vertical(state, delta)

    def nav_horizontal(delta):
        return lst.nav_horizontal(state, delta)

    def nav_page(delta):
        return lst.nav_page(state, delta)

    def nav_lb_rb(delta):
        return lst.nav_lb_rb(state, delta)

    def _truncate_to_width(font, text, max_w):
        return tiles._truncate_to_width(state, font, text, max_w)

    def draw_tiles_view():
        return tiles.draw_tiles_view(state)

    # Overlay menus: None | "system" | "settings"  (B / Esc)
    system_menu_items = [
        {"key": "resume", "label": "Resume"},
        {"key": "settings", "label": "Settings"},
        {"key": "input_remap_open", "label": "Controller mapping"},
        {"key": "exit", "label": "Exit launcher"},
        {"key": "shutdown", "label": "Shut down PC"},
        {"key": "reboot", "label": "Reboot PC"},
    ]
    state.system_menu_items = system_menu_items
    state.games = games
    state.settings_menu_items = []
    state.settings_cum_starts = []
    state.settings_row_specs = []
    state.settings_content_h = 0
    state.overlay_menu = None
    state.overlay_index = 0
    state.overlay_scroll_y = 0
    state.input_remap_session = None

    def _settings_first_row():
        return ovl._settings_first_row(state)

    def rebuild_settings_layout():
        return ovl.rebuild_settings_layout(state)

    rebuild_settings_layout()

    def overlay_items():
        return ovl.overlay_items(state)

    def _overlay_snap_scroll():
        return ovl._overlay_snap_scroll(state)

    def overlay_move(delta):
        return ovl.overlay_move(state, delta)

    def reload_fonts_and_layout():
        return ovl.reload_fonts_and_layout(state)

    def apply_setting_live(key):
        return ovl.apply_setting_live(state, key)

    def overlay_back():
        return ovl.overlay_back(state)

    def overlay_confirm():
        return ovl.overlay_confirm(state)

    clock = pygame.time.Clock()
    state.running = True
    trig_page_arm_lt = True
    trig_page_arm_rt = True
    active_remap_proc = [None]

    def stop_active_remap():
        if active_remap_proc[0]:
            from joypad.input.worker import stop_remap_worker

            stop_remap_worker(active_remap_proc[0])
            active_remap_proc[0] = None

    import atexit

    atexit.register(stop_active_remap)

    def try_launch_game(g):
        """Launches game g. Returns (exit_launcher, axis_held) or None on skip."""
        from joypad.input.profiles import resolve_profile_path
        from joypad.input.worker import start_remap_worker, stop_remap_worker

        platform = g.get("platform")
        process = None
        skip_restore = False
        remap_proc = None
        profile_path = resolve_profile_path(config, g, _BASE_DIR) if sys.platform == "win32" else None
        if sys.platform == "win32":
            from joypad.input.log import init_remap_log, remap_log, remap_log_enabled
            from joypad.input.profiles import game_remap_key

            if remap_log_enabled(config):
                init_remap_log(_BASE_DIR, enabled=True)
                remap_log(
                    "launch %s key=%s profile=%s"
                    % (g.get("name"), game_remap_key(g), profile_path or "(none)")
                )
        if platform == "steam":
            if not steam_path:
                if not state.overlay_menu:
                    print("Steam not found. Specify steam_path in config.json")
                return None
            aid = g.get("steam_app_id")
            if not aid:
                return None
            args = g.get("launch_args") or default_args.get("steam", "-fullscreen")
            process = launch_steam_game(steam_path, aid, args, state.steam_start_args)
            skip_restore = str(aid) in steam_skip_restore_ids
        elif platform == "epic":
            exe = g.get("exe_path")
            if not exe:
                return None
            args = g.get("launch_args") or default_args.get("epic", "-fullscreen")
            process = launch_epic_game(exe, args)
        elif platform == "nsp":
            nsp_path = g.get("nsp_path")
            if not nsp_path or not os.path.isfile(nsp_path):
                return None
            assoc_cfg = config.get("nsp_use_windows_association")
            if assoc_cfg is None:
                use_association = sys.platform == "win32"
            else:
                use_association = bool(assoc_cfg)
            emu = (config.get("nsp_emulator_path") or "").strip()
            args = g.get("launch_args")
            if args is None:
                extra = (default_args.get("nsp") or config.get("nsp_launch_args") or "").strip()
            else:
                extra = (args or "").strip()
            process = launch_nsp_game(emu, nsp_path, extra, use_association=use_association)
            if process is None and not state.overlay_menu:
                print(
                    "NSP: launch failed. On Windows set .nsp to open with your emulator (e.g. Ryujinx), "
                    "or set a valid nsp_emulator_path in config.json."
                )
        elif platform == "system":
            action = g.get("system_action")
            if action:
                perform_system_action(action)
                return (True, 0)
            return None
        else:
            return None
        if not process:
            return None
        from joypad.input.watch import game_watch_targets

        watch_exe, watch_dir = game_watch_targets(g)
        if profile_path:
            remap_proc = start_remap_worker(
                profile_path,
                process.pid,
                _BASE_DIR,
                watch_exe=watch_exe,
                watch_dir=watch_dir,
                parent_pid=os.getpid(),
                log_enabled=remap_log_enabled(config),
            )
            active_remap_proc[0] = remap_proc
        try:
            _yield_for_game_window(2.0)
            if process and platform == "epic":
                _bring_game_to_foreground(process, 12)
            elif process and platform == "steam":
                _bring_game_to_foreground(process, 20)
            elif process and platform == "nsp":
                _bring_game_to_foreground(process, 12)
            elif process:
                _bring_process_window_to_foreground(process.pid)
                _yield_for_game_window(0.5)
                _bring_process_window_to_foreground(process.pid)
            _send_launcher_to_back(hwnd)
            pygame.display.iconify()
            if not skip_restore:
                _wait_for_game_and_restore(
                    process, hwnd, platform, watch_exe=watch_exe, watch_dir=watch_dir, remap_proc=remap_proc
                )
        finally:
            stop_remap_worker(remap_proc)
            active_remap_proc[0] = None
        return (False, 15)

    state.try_launch_game = try_launch_game
    state.stop_active_remap = stop_active_remap

    state.title_surface, state.hint_surface = _hint_surfaces()

    def show_launching_overlay(_game_name=None):
        return ovl.show_launching_overlay(state, _game_name)

    while state.running:
        frames_since_rescan += 1
        if frames_since_rescan >= RESCAN_INTERVAL:
            frames_since_rescan = 0
            joysticks = rescan_joysticks()

        try:
            events = pygame.event.get()
        except (KeyError, SystemError):
            events = []

        if state.input_remap_session:
            for event in events:
                if event.type == pygame.QUIT:
                    state.running = False
            state.input_remap_session.process_events(events)
            if axis_held <= 0 and joysticks:
                stick = joysticks[0]
                y = stick.get_axis(AXIS_LEFT_Y)
                x = stick.get_axis(AXIS_LEFT_X)
                if y < -DEADZONE:
                    state.input_remap_session._nav(-1)
                    axis_held = AXIS_REPEAT_FRAMES
                elif y > DEADZONE:
                    state.input_remap_session._nav(1)
                    axis_held = AXIS_REPEAT_FRAMES
                elif state.input_remap_session.mode == "editor" and x < -DEADZONE:
                    state.input_remap_session._nav_h(-1)
                    axis_held = AXIS_REPEAT_FRAMES
                elif state.input_remap_session.mode == "editor" and x > DEADZONE:
                    state.input_remap_session._nav_h(1)
                    axis_held = AXIS_REPEAT_FRAMES
            if axis_held > 0:
                axis_held -= 1
            state.input_remap_session.draw()
            pygame.display.flip()
            clock.tick(60)
            if state.input_remap_session.finished:
                state.input_remap_session = None
            continue

        for event in events:
            if event.type == pygame.QUIT:
                state.running = False
            if event.type == getattr(pygame, "JOYDEVICEADDED", None):
                joysticks = rescan_joysticks()
            if event.type == pygame.KEYDOWN:
                if state.overlay_menu:
                    if event.key == pygame.K_ESCAPE:
                        overlay_back()
                    if event.key == pygame.K_UP:
                        overlay_move(-1)
                    if event.key == pygame.K_DOWN:
                        overlay_move(1)
                    if event.key == pygame.K_RETURN:
                        overlay_confirm()
                else:
                    if event.key == pygame.K_ESCAPE:
                        state.overlay_menu = "system"
                        state.overlay_index = 0
                    if event.key == pygame.K_UP:
                        nav_vertical(-1)
                    if event.key == pygame.K_DOWN:
                        nav_vertical(1)
                    if event.key == pygame.K_LEFT:
                        nav_horizontal(-1)
                    if event.key == pygame.K_RIGHT:
                        nav_horizontal(1)
                    if event.key == pygame.K_PAGEUP:
                        nav_page(-1)
                    if event.key == pygame.K_PAGEDOWN:
                        nav_page(1)
                    if event.key == pygame.K_RETURN:
                        it = get_selected_item()
                        if not it:
                            continue
                        g = it["game"]
                        if g.get("platform") in ("steam", "epic", "nsp"):
                            show_launching_overlay(g.get("name", "Game"))
                        result = try_launch_game(g)
                        if result is not None:
                            should_exit, axis_held_val = result
                            if should_exit:
                                state.running = False
                                break
                            axis_held = axis_held_val

            if event.type == pygame.JOYBUTTONDOWN:
                if state.overlay_menu:
                    if event.button == BTN_B or event.button == BTN_BACK:
                        overlay_back()
                    if event.button == BTN_A or event.button == BTN_START:
                        overlay_confirm()
                else:
                    if event.button == BTN_A or event.button == BTN_START:
                        it = get_selected_item()
                        if not it:
                            continue
                        g = it["game"]
                        if g.get("platform") in ("steam", "epic", "nsp"):
                            show_launching_overlay(g.get("name", "Game"))
                        result = try_launch_game(g)
                        if result is not None:
                            should_exit, axis_held_val = result
                            if should_exit:
                                state.running = False
                                break
                            axis_held = axis_held_val
                    if event.button == BTN_B or event.button == BTN_BACK:
                        state.overlay_menu = "system"
                        state.overlay_index = 0
                    elif event.button == BTN_LB:
                        nav_lb_rb(-1)
                    elif event.button == BTN_RB:
                        nav_lb_rb(1)

            if event.type == pygame.JOYAXISMOTION and event.axis == AXIS_LEFT_Y:
                if axis_held <= 0:
                    if state.overlay_menu:
                        if event.value < -DEADZONE:
                            overlay_move(-1)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value > DEADZONE:
                            overlay_move(1)
                            axis_held = AXIS_REPEAT_FRAMES
                    else:
                        if event.value < -DEADZONE:
                            nav_vertical(-1)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value > DEADZONE:
                            nav_vertical(1)
                            axis_held = AXIS_REPEAT_FRAMES
            elif event.type == pygame.JOYAXISMOTION and event.axis == AXIS_LEFT_X:
                if not state.overlay_menu and axis_held <= 0:
                    if event.value < -DEADZONE:
                        nav_horizontal(-1)
                        axis_held = AXIS_REPEAT_FRAMES
                    elif event.value > DEADZONE:
                        nav_horizontal(1)
                        axis_held = AXIS_REPEAT_FRAMES
            elif event.type == pygame.JOYAXISMOTION:
                if not state.overlay_menu and axis_held <= 0:
                    if event.axis == 5 and event.value > 0.72:
                        if trig_page_arm_rt:
                            nav_page(1)
                            trig_page_arm_rt = False
                            axis_held = AXIS_REPEAT_FRAMES * 2
                    elif event.axis == 5 and event.value < 0.2:
                        trig_page_arm_rt = True
                    if event.axis == 4 and event.value > 0.72:
                        if trig_page_arm_lt:
                            nav_page(-1)
                            trig_page_arm_lt = False
                            axis_held = AXIS_REPEAT_FRAMES * 2
                    elif event.axis == 4 and event.value < 0.2:
                        trig_page_arm_lt = True
            if event.type == pygame.JOYHATMOTION and event.hat == 0:
                if axis_held <= 0:
                    if state.overlay_menu:
                        if event.value[1] > 0:
                            overlay_move(-1)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value[1] < 0:
                            overlay_move(1)
                            axis_held = AXIS_REPEAT_FRAMES
                    else:
                        if event.value[1] > 0:
                            nav_vertical(-1)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value[1] < 0:
                            nav_vertical(1)
                            axis_held = AXIS_REPEAT_FRAMES
                        if event.value[0] < 0:
                            nav_horizontal(-1)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value[0] > 0:
                            nav_horizontal(1)
                            axis_held = AXIS_REPEAT_FRAMES

        if axis_held > 0:
            axis_held -= 1

        if not state.overlay_menu and joysticks and axis_held <= 0:
            stick = joysticks[0]
            y = stick.get_axis(AXIS_LEFT_Y)
            x = stick.get_axis(AXIS_LEFT_X)
            if y < -DEADZONE:
                nav_vertical(-1)
                axis_held = AXIS_REPEAT_FRAMES
            elif y > DEADZONE:
                nav_vertical(1)
                axis_held = AXIS_REPEAT_FRAMES
            elif x < -DEADZONE:
                nav_horizontal(-1)
                axis_held = AXIS_REPEAT_FRAMES
            elif x > DEADZONE:
                nav_horizontal(1)
                axis_held = AXIS_REPEAT_FRAMES

        if state.ui_mode == "tiles" and state.tile_snap_scroll:
            _tile_snap_scroll()

        # Keep selected row on screen only when navigating with ↑↓ / stick (page scroll must not snap back).
        if state.ui_mode == "list" and state.list_snap_scroll_to_selection:
            sel_top = state.cum_starts[state.selected]
            sel_h = state.row_specs[state.selected]["height"]
            sel_bot = sel_top + sel_h
            if sel_top < scroll_y:
                scroll_y = sel_top
            elif sel_bot > scroll_y + state.viewport_h:
                scroll_y = sel_bot - state.viewport_h
        scroll_y = max(0, min(scroll_y, state.max_scroll_y))

        # Rendering
        if state.bg_surface:
            screen.blit(state.bg_surface, (0, 0))
        else:
            screen.fill(state.bg_color)
        screen.blit(state.title_surface, (60, 40))
        hint_bottom = state.tile_geom["bottom_hint"] if state.ui_mode == "tiles" else state.list_bottom_margin
        screen.blit(state.hint_surface, (60, h - hint_bottom))

        if state.ui_mode == "tiles":
            draw_tiles_view()
        else:
            prev_clip = screen.get_clip()
            screen.set_clip(pygame.Rect(0, state.list_start_y, w, state.viewport_h))
            try:
                for idx in range(len(list_items)):
                    y_content = state.cum_starts[idx]
                    rh = state.row_specs[idx]["height"]
                    screen_y = state.list_start_y + y_content - scroll_y
                    if screen_y + rh < state.list_start_y or screen_y > state.list_start_y + state.viewport_h:
                        continue
                    spec = state.row_specs[idx]
                    if spec["kind"] == "header":
                        text = state.font_category.render("  %s" % spec["title"], True, state.title_color)
                        screen.blit(text, (60, screen_y))
                    else:
                        color = state.highlight_color if idx == state.selected else state.text_color
                        screen.blit(state.font_list.render(spec["prefix"], True, color), (list_left, screen_y))
                        ly = screen_y
                        for chunk in spec["name_lines"]:
                            surf = state.font_list.render(chunk, True, color)
                            screen.blit(surf, (spec["x_text"], ly))
                            ly += state.list_line_skip
            finally:
                screen.set_clip(prev_clip)

            if state.max_scroll_y > 0:
                if scroll_y > 0:
                    up_arrow = state.font_list.render(" ▲", True, state.title_color)
                    screen.blit(up_arrow, (w - 50, state.list_start_y + 4))
                if scroll_y < state.max_scroll_y:
                    down_arrow = state.font_list.render(" ▼", True, state.title_color)
                    screen.blit(down_arrow, (w - 50, state.list_start_y + state.viewport_h - state.font_list.get_linesize() - 4))

        if state.overlay_menu:
            menu_width = min(w - 80, 860)
            header_h = 48
            max_menu_h = max(120, h - 80)

            if state.overlay_menu == "settings":
                content_h = state.settings_content_h
                menu_height = min(content_h + header_h, max_menu_h)
                body_h = menu_height - header_h
                max_overlay_scroll = max(0, content_h - body_h)
                overlay_scroll_y_clamped = max(0, min(state.overlay_scroll_y, max_overlay_scroll))
                menu_x = (w - menu_width) // 2
                menu_y = (h - menu_height) // 2 - 10

                pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))
                pygame.draw.rect(screen, state.title_color, (menu_x, menu_y, menu_width, menu_height), 2)

                menu_title = state.font_title.render("Settings", True, state.title_color)
                title_x = menu_x + (menu_width - menu_title.get_width()) // 2
                screen.blit(menu_title, (title_x, menu_y + 8))

                body_top = menu_y + header_h
                prev_clip = screen.get_clip()
                screen.set_clip(pygame.Rect(menu_x, body_top, menu_width, body_h))
                try:
                    for idx, spec in enumerate(state.settings_row_specs):
                        y_content = state.settings_cum_starts[idx]
                        rh = spec["height"]
                        row_y = body_top + y_content - overlay_scroll_y_clamped
                        if row_y + rh < body_top or row_y > body_top + body_h:
                            continue
                        if spec["kind"] == "header":
                            text = state.font_category.render("  %s" % spec["title"], True, state.title_color)
                            screen.blit(text, (menu_x + 20, row_y))
                        else:
                            item = spec["item"]
                            color = state.highlight_color if idx == state.overlay_index else state.text_color
                            text = state.font_list.render(item["label"], True, color)
                            row_x = menu_x + max(20, (menu_width - text.get_width()) // 2)
                            screen.blit(text, (row_x, row_y))
                finally:
                    screen.set_clip(prev_clip)
            else:
                items = overlay_items()
                menu_line_h = state.font_list.get_linesize() + 8
                content_h = len(items) * menu_line_h
                menu_height = min(content_h + header_h, max_menu_h)
                body_h = menu_height - header_h
                max_overlay_scroll = max(0, content_h - body_h)
                overlay_scroll_y_clamped = max(0, min(state.overlay_scroll_y, max_overlay_scroll))
                menu_x = (w - menu_width) // 2
                menu_y = (h - menu_height) // 2 - 10

                pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))
                pygame.draw.rect(screen, state.title_color, (menu_x, menu_y, menu_width, menu_height), 2)

                menu_title = state.font_title.render("System menu", True, state.title_color)
                title_x = menu_x + (menu_width - menu_title.get_width()) // 2
                screen.blit(menu_title, (title_x, menu_y + 8))

                body_top = menu_y + header_h
                prev_clip = screen.get_clip()
                screen.set_clip(pygame.Rect(menu_x, body_top, menu_width, body_h))
                try:
                    for idx, item in enumerate(items):
                        color = state.highlight_color if idx == state.overlay_index else state.text_color
                        text = state.font_list.render(item["label"], True, color)
                        row_y = body_top + idx * menu_line_h - overlay_scroll_y_clamped
                        if row_y + menu_line_h < body_top or row_y > body_top + body_h:
                            continue
                        row_x = menu_x + max(20, (menu_width - text.get_width()) // 2)
                        screen.blit(text, (row_x, row_y))
                finally:
                    screen.set_clip(prev_clip)

            if max_overlay_scroll > 0:
                if overlay_scroll_y_clamped > 0:
                    up_arrow = state.font_list.render(" ▲", True, state.title_color)
                    screen.blit(up_arrow, (menu_x + menu_width - 36, body_top + 2))
                if overlay_scroll_y_clamped < max_overlay_scroll:
                    down_arrow = state.font_list.render(" ▼", True, state.title_color)
                    screen.blit(down_arrow, (menu_x + menu_width - 36, body_top + body_h - state.font_list.get_linesize() - 2))

        pygame.display.flip()
        clock.tick(60)

    stop_active_remap()
    pygame.quit()


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    if len(argv) >= 2 and argv[1] == "--input-remap-worker":
        from joypad.input.worker import run_remap_worker_main
        run_remap_worker_main()
        return 0
    try:
        run()
        return 0
    except BaseException:
        import traceback
        log_path = os.path.join(_BASE_DIR, "launcher_error.log")
        err_text = traceback.format_exc()
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err_text)
        except Exception:
            pass
        traceback.print_exc()
        _show_error_message("Launch error.\nDetails written to:\n%s" % log_path)
        return 1
