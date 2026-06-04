#!/usr/bin/env python3
"""Input remap editor session (pygame UI)."""

import os

from joypad.input.profiles import (
    assign_game_profile,
    get_assigned_profile_id,
    list_remapped_games,
    load_default_profile,
    load_profile,
    profile_file_path,
    save_profile,
    suggest_profile_id,
)
from joypad.integrations import REMAP_ELIGIBLE_PLATFORMS
from joypad.ui.editor.grid_scroll import scroll_grid as _scroll_grid
from joypad.ui.editor.grid_scroll import snap_grid_scroll as _snap_grid_scroll
from joypad.ui.editor.slots import (
    BOOL_SLOT_KINDS,
    NUMERIC_SLOT_KINDS,
    _adjust_numeric_slot,
    _apply_slot_value,
    _cycle_slot,
    build_editor_slots,
)


class InputRemapSession:
    """Full-screen UI: game list → visual mapping editor."""

    def __init__(self, screen, fonts, colors, config, games, base_dir, save_config_fn):
        self.screen = screen
        self.font_title, self.font_list, self.font_hint = fonts
        self.bg, self.text, self.highlight, self.title = colors
        self.config = config
        self.all_games = games
        self.base_dir = base_dir
        self.save_config = save_config_fn
        self.finished = False
        self.mode = "game_list"
        self.game_index = 0
        self.pick_index = 0
        self.slot_index = 0
        self.scroll = 0
        self.current_game = None
        self.profile = None
        self.profile_path = None
        self.slots = []
        self._pad_img = None
        self._pad_img_key = None
        self._trig_arm_lt = True
        self._trig_arm_rt = True
        self._refresh_game_list()

    def _refresh_game_list(self):
        self.remapped = list_remapped_games(self.config, self.all_games)
        self.pick_candidates = [g for g in self.all_games if g.get("platform") in REMAP_ELIGIBLE_PLATFORMS]
        if self.game_index >= len(self.remapped):
            self.game_index = max(0, len(self.remapped) - 1)

    def _load_editor_for_game(self, game):
        self.current_game = game
        pid = get_assigned_profile_id(self.config, game)
        if not pid:
            pid = suggest_profile_id(game)
            assign_game_profile(self.config, game, pid, self.base_dir)
            self.save_config(self.config)
        self.profile_path = profile_file_path(self.config, self.base_dir, pid)
        if os.path.isfile(self.profile_path):
            self.profile = load_profile(self.profile_path, self.base_dir, self.config)
        else:
            self.profile = load_default_profile(
                self.base_dir, self.config, name=game.get("name") or pid
            )
            save_profile(self.profile_path, self.profile)
        self.slots = build_editor_slots(self.profile)
        self.slot_index = 0
        self.scroll = 0
        self._trig_arm_lt = True
        self._trig_arm_rt = True
        self.mode = "editor"

    def process_events(self, events, axis_nav=None):
        from joypad.ui.editor import input as editor_input

        return editor_input.process_events(self, events, axis_nav)

    def _snap_grid_scroll(self, areas=None):
        _snap_grid_scroll(self, areas)

    def scroll_grid(self, delta_pages):
        _scroll_grid(self, delta_pages)

    def _cycle_current_slot(self):
        slot = self.slots[self.slot_index]
        if slot["kind"] in NUMERIC_SLOT_KINDS:
            new_val = _adjust_numeric_slot(self.profile, slot, 1)
        elif slot["kind"] in BOOL_SLOT_KINDS:
            new_val = not bool(slot["value"])
        else:
            new_val = _cycle_slot(self.profile, slot)
        slot["value"] = new_val
        _apply_slot_value(self.profile, slot, new_val)
        save_profile(self.profile_path, self.profile)

    def _reset_slot(self):
        slot = self.slots[self.slot_index]
        if slot["kind"] in NUMERIC_SLOT_KINDS:
            new_val = _adjust_numeric_slot(self.profile, slot, -1)
            slot["value"] = new_val
            _apply_slot_value(self.profile, slot, new_val)
            save_profile(self.profile_path, self.profile)
            return
        if slot["kind"] in BOOL_SLOT_KINDS:
            new_val = False
            slot["value"] = new_val
            _apply_slot_value(self.profile, slot, new_val)
            save_profile(self.profile_path, self.profile)
            return
        if slot["kind"] in ("left_stick", "right_stick", "trigger", "button", "dpad", "chord", "stick_click"):
            new_val = "none"
            slot["value"] = new_val
            _apply_slot_value(self.profile, slot, new_val)
            save_profile(self.profile_path, self.profile)

    def draw(self):
        from joypad.ui.editor import drawing

        drawing.draw(self)
