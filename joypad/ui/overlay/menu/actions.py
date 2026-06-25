"""Overlay menu confirm/back and system actions."""

from joypad.config.loader import save_config
from joypad.config.settings import apply_setting_toggle
from joypad.launch.launcher import perform_system_action
from joypad.paths import _BASE_DIR
from joypad.ui.overlay.menu.layout import open_settings_overlay, rebuild_settings_layout, settings_first_row
from joypad.ui.overlay.menu.live import apply_setting_live


def overlay_back(state):
    if state.overlay_menu == "settings":
        state.overlay_menu = "system"
        state.overlay_index = 0
    else:
        state.overlay_menu = None
        state.overlay_index = 0


def _open_input_remap(state):
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


def overlay_confirm(state):
    if state.overlay_menu == "system":
        item = state.system_menu_items[state.overlay_index]
        key = item["key"]
        if key == "resume":
            state.overlay_menu = None
            state.overlay_index = 0
        elif key == "settings":
            open_settings_overlay(state)
        elif key == "input_remap_open":
            _open_input_remap(state)
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
            _open_input_remap(state)
        elif apply_setting_toggle(state.config, key):
            apply_setting_live(state, key)
