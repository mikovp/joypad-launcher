#!/usr/bin/env python3
"""Visual gamepad mapping editor (pygame)."""

import os
import sys

import pygame

from joypad.input.bindings import (
    DPAD_BINDINGS,
    binding_label,
    cycle_binding,
    cycle_right_stick_mode,
    cycle_stick_mode,
)
from joypad.input.constants import (
    BTN_A,
    BTN_B,
    BTN_BACK,
    BTN_LB,
    BTN_RB,
    BTN_START,
    BTN_X,
    BTN_Y,
)
from joypad.input.profiles import (
    assign_game_profile,
    ensure_chords,
    format_slot_binding,
    game_remap_key,
    get_assigned_profile_id,
    list_remapped_games,
    load_default_profile,
    load_profile,
    parse_chord_slot_key,
    parse_slot_binding,
    profile_file_path,
    save_profile,
    suggest_profile_id,
    unassign_game,
)

# Re-export button constants for layout
BTN_LAYOUT = [
    ("btn_%d" % BTN_A, "A", BTN_A),
    ("btn_%d" % BTN_B, "B", BTN_B),
    ("btn_%d" % BTN_X, "X", BTN_X),
    ("btn_%d" % BTN_Y, "Y", BTN_Y),
    ("btn_%d" % BTN_LB, "LB", BTN_LB),
    ("btn_%d" % BTN_RB, "RB", BTN_RB),
    ("btn_%d" % BTN_BACK, "Back", BTN_BACK),
    ("btn_%d" % BTN_START, "Start", BTN_START),
]

STICK_MODE_LABELS = {
    "none": "—",
    "wasd": "WASD",
    "arrows": "Arrows",
    "mouse": "Mouse",
}


def _stick_label(mode):
    return STICK_MODE_LABELS.get(mode, mode or "—")


# Порядок ↑↓ в редакторе: как на экране (плечи → сетка → аккорды → настройки)
def _face_nav_entries():
    face = [
        (BTN_A, "A"),
        (BTN_B, "B"),
        (BTN_X, "X"),
        (BTN_Y, "Y"),
    ]
    entries = []
    for idx, short in face:
        entries.append(("button", str(idx), short))
        entries.append(("chord", "lb_%d" % idx, "LB + %s" % short))
        entries.append(("chord", "rb_%d" % idx, "RB + %s" % short))
    return entries


EDITOR_NAV_ORDER = [
    ("button", str(BTN_LB), "Left bumper"),
    ("trigger", "left", "Left trigger"),
    ("button", str(BTN_BACK), "Back"),
    ("left_stick", None, "Joystick"),
    ("stick_click", "left", "L-stick click"),
    ("dpad", "dpad_up", "D-Up"),
    ("dpad", "dpad_down", "D-Down"),
    ("dpad", "dpad_left", "D-Left"),
    ("dpad", "dpad_right", "D-Right"),
    ("button", str(BTN_RB), "Right bumper"),
    ("trigger", "right", "Right trigger"),
    ("button", str(BTN_START), "Start"),
    ("right_stick", None, "Joystick"),
    ("stick_click", "right", "R-stick click"),
] + _face_nav_entries() + [
    ("mouse_sens", None, "Mouse speed"),
    ("mouse_scale", None, "Mouse scale"),
    ("deadzone", None, "Deadzone"),
    ("mouse_accel", None, "Mouse accel"),
    ("mouse_accel_off_lt", None, "Accel off LT"),
]

NUMERIC_SLOT_KINDS = ("mouse_sens", "mouse_scale", "deadzone", "mouse_accel")
NUMERIC_SLOT_STEPS = {
    "mouse_sens": ("mouse_sensitivity", 0.1, 0.1, 50.0),
    "mouse_scale": ("mouse_scale", 0.1, 0.1, 10.0),
    "deadzone": ("deadzone", 0.01, 0.0, 1.0),
    "mouse_accel": ("mouse_acceleration", 0.05, 0.0, 2.0),
}
BOOL_SLOT_KINDS = ("mouse_accel_off_lt",)


def _round_numeric(kind, value):
    if kind in ("deadzone", "mouse_accel"):
        return round(float(value), 2)
    return round(float(value), 1)


def _adjust_numeric_slot(profile, slot, direction):
    kind = slot["kind"]
    if kind not in NUMERIC_SLOT_STEPS:
        return slot["value"]
    _, step, min_v, max_v = NUMERIC_SLOT_STEPS[kind]
    new_v = _round_numeric(kind, float(slot["value"]) + direction * step)
    new_v = max(min_v, min(max_v, new_v))
    return new_v


def build_editor_slots(profile):
    """Editable controls in on-screen navigation order."""
    buttons = profile.get("buttons") or {}
    triggers = profile.get("triggers") or {}
    dpad = profile.get("dpad") or {}
    chords = ensure_chords(profile)
    stick_clicks = profile.get("stick_clicks") or {}

    def _value(kind, key):
        if kind == "left_stick":
            return profile.get("left_stick") or "none"
        if kind == "right_stick":
            return profile.get("right_stick") or "none"
        if kind == "stick_click":
            return parse_slot_binding(stick_clicks.get(key, "none"))[0]
        if kind == "trigger":
            return triggers.get(key, "none")
        if kind == "button":
            return buttons.get(key, "none")
        if kind == "chord":
            parsed = parse_chord_slot_key(key)
            if parsed:
                mod, face = parsed
                return (chords.get(mod) or {}).get(face, "none")
            return "none"
        if kind == "dpad":
            return dpad.get(key, "none")
        if kind == "mouse_sens":
            return profile["mouse_sensitivity"]
        if kind == "mouse_scale":
            return profile["mouse_scale"]
        if kind == "deadzone":
            return profile["deadzone"]
        if kind == "mouse_accel":
            return profile.get("mouse_acceleration", 0.0)
        if kind == "mouse_accel_off_lt":
            return bool(profile.get("mouse_accel_off_lt", False))
        return "none"

    slots = []
    for kind, key, label in EDITOR_NAV_ORDER:
        slot = {"kind": kind, "label": label, "value": _value(kind, key)}
        if key is not None:
            slot["key"] = key
        if kind == "button":
            slot["slot_id"] = "btn_%s" % key
        slots.append(slot)
    return slots


def _apply_slot_value(profile, slot, value):
    if slot["kind"] == "left_stick":
        profile["left_stick"] = value
    elif slot["kind"] == "right_stick":
        profile["right_stick"] = value
    elif slot["kind"] == "stick_click":
        section = profile.setdefault("stick_clicks", {})
        prev = section.get(slot["key"])
        _, mode = parse_slot_binding(prev)
        section[slot["key"]] = format_slot_binding(value, mode)
    elif slot["kind"] == "trigger":
        profile.setdefault("triggers", {})[slot["key"]] = value
    elif slot["kind"] == "button":
        profile.setdefault("buttons", {})[slot["key"]] = value
    elif slot["kind"] == "chord":
        parsed = parse_chord_slot_key(slot["key"])
        if parsed:
            mod, face = parsed
            ensure_chords(profile)[mod][face] = value
    elif slot["kind"] == "dpad":
        profile.setdefault("dpad", {})[slot["key"]] = value
    elif slot["kind"] == "mouse_sens":
        profile["mouse_sensitivity"] = value
    elif slot["kind"] == "mouse_scale":
        profile["mouse_scale"] = value
    elif slot["kind"] == "deadzone":
        profile["deadzone"] = value
    elif slot["kind"] == "mouse_accel":
        profile["mouse_acceleration"] = value
    elif slot["kind"] == "mouse_accel_off_lt":
        profile["mouse_accel_off_lt"] = bool(value)


def _cycle_slot(profile, slot):
    cur = slot["value"]
    kind = slot["kind"]
    if kind == "left_stick":
        return cycle_stick_mode(cur)
    if kind == "right_stick":
        return cycle_right_stick_mode(cur)
    return cycle_binding(cur)


FACE_BTN_COLORS = {
    str(BTN_A): (107, 191, 89),
    str(BTN_B): (191, 77, 77),
    str(BTN_X): (77, 130, 191),
    str(BTN_Y): (191, 176, 77),
}

OUTLINE_COLOR = (150, 156, 170)
PAD_IMAGE_FILE = "xbox-controller-clipart-md.png"
PAD_IMAGE_ASPECT = 800 / 549
# Normalized centers on xbox-controller-clipart-md.png (800×549)
PAD_LAYOUT = {
    "ls": (0.244, 0.415),
    "rs": (0.618, 0.664),
    "dpad": (0.378, 0.660),
    "lb": (0.231, 0.121),
    "rb": (0.767, 0.121),
    "lt": (0.251, 0.054),
    "rt": (0.748, 0.054),
    "back": (0.395, 0.415),
    "start": (0.600, 0.416),
    "face": {
        str(BTN_A): (0.752, 0.379),
        str(BTN_B): (0.822, 0.285),
        str(BTN_X): (0.682, 0.280),
        str(BTN_Y): (0.752, 0.181),
    },
}
PAD_RADIUS = {
    "stick": 0.048,
    "stick_click": 0.040,
    "face": 0.040,
    "dpad": 0.052,
    "shoulder": 0.050,
    "trigger": 0.046,
    "center": 0.030,
}
PANEL_FILL = (32, 35, 46)
PANEL_SEL = (55, 62, 82)


def _slot_index(slots, kind, key=None):
    for i, slot in enumerate(slots):
        if slot.get("kind") != kind:
            continue
        if key is None or slot.get("key") == key:
            return i
    return None


def _pad_hotspot(slot):
    """Return (nx, ny, radius_scale_key) for pad overlay or None."""
    kind = slot.get("kind")
    key = slot.get("key")
    if kind == "left_stick":
        return PAD_LAYOUT["ls"], "stick"
    if kind == "stick_click" and key == "left":
        return PAD_LAYOUT["ls"], "stick_click"
    if kind == "right_stick":
        return PAD_LAYOUT["rs"], "stick"
    if kind == "stick_click" and key == "right":
        return PAD_LAYOUT["rs"], "stick_click"
    if kind == "dpad":
        return PAD_LAYOUT["dpad"], "dpad"
    if kind == "trigger" and key == "left":
        return PAD_LAYOUT["lt"], "trigger"
    if kind == "trigger" and key == "right":
        return PAD_LAYOUT["rt"], "trigger"
    if kind == "button":
        if key == str(BTN_LB):
            return PAD_LAYOUT["lb"], "shoulder"
        if key == str(BTN_RB):
            return PAD_LAYOUT["rb"], "shoulder"
        if key == str(BTN_BACK):
            return PAD_LAYOUT["back"], "center"
        if key == str(BTN_START):
            return PAD_LAYOUT["start"], "center"
        if key in PAD_LAYOUT["face"]:
            return PAD_LAYOUT["face"][key], "face"
    if kind == "chord":
        parsed = parse_chord_slot_key(key)
        if parsed:
            _, face = parsed
            pt = PAD_LAYOUT["face"].get(face)
            if pt:
                return pt, "face"
    return None


def _truncate_text(font, text, max_w):
    text = text or ""
    if max_w < 8 or font.size(text)[0] <= max_w:
        return text
    ell = "..."
    for n in range(len(text), 0, -1):
        trial = text[:n] + ell
        if font.size(trial)[0] <= max_w:
            return trial
    return ell


def _fit_row_label_value(font_label, font_val, label, value, width, gap=12):
    value = value or ""
    val_s = font_val.render(value, True, (255, 255, 255))
    val_w = val_s.get_width()
    label_max = max(20, width - val_w - gap)
    label_txt = _truncate_text(font_label, label, label_max)
    label_s = font_label.render(label_txt, True, (255, 255, 255))
    while label_s.get_width() + val_w + gap > width and len(label_txt) > 1:
        label_txt = _truncate_text(font_label, label_txt, label_max - 8)
        label_s = font_label.render(label_txt, True, (255, 255, 255))
        label_max -= 8
    return label_s, val_s, label_max


def _slot_display(slot):
    kind = slot["kind"]
    val = slot["value"]
    if kind in ("left_stick", "right_stick"):
        return _stick_label(val)
    if kind == "mouse_sens":
        return "%.1f" % float(val)
    if kind == "mouse_scale":
        return "%.1f" % float(val)
    if kind == "deadzone":
        return "%.2f" % float(val)
    if kind == "mouse_accel":
        return "%.2f" % float(val)
    if kind == "mouse_accel_off_lt":
        return "On" if val else "Off"
    return binding_label(val)


FACE_COL_INDEX = 3


def _grid_column_specs(slots):
    face_keys = {str(BTN_A), str(BTN_B), str(BTN_X), str(BTN_Y)}
    return [
        (
            "LEFT STICK",
            [
                _slot_index(slots, "left_stick"),
                _slot_index(slots, "stick_click", "left"),
            ],
        ),
        ("D-PAD", [_slot_index(slots, "dpad", k) for k, _ in DPAD_BINDINGS]),
        (
            "RIGHT STICK",
            [
                _slot_index(slots, "right_stick"),
                _slot_index(slots, "stick_click", "right"),
            ],
        ),
        (
            "FACE + CHORDS",
            [
                idx
                for idx, slot in enumerate(slots)
                if (
                    slot.get("kind") == "button"
                    and slot.get("key") in face_keys
                )
                or (
                    slot.get("kind") == "chord"
                    and slot.get("key", "").startswith(("lb_", "rb_"))
                )
            ],
        ),
    ]


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

    def _gamepad_image_path(self):
        rel = os.path.join("assets", PAD_IMAGE_FILE)
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            bundled = os.path.join(sys._MEIPASS, rel)
            if os.path.isfile(bundled):
                return bundled
        return os.path.join(self.base_dir, rel)

    def _get_gamepad_image(self, target_w, target_h):
        key = (max(1, int(target_w)), max(1, int(target_h)))
        if self._pad_img_key == key and self._pad_img is not None:
            return self._pad_img
        path = self._gamepad_image_path()
        if not os.path.isfile(path):
            self._pad_img = None
            self._pad_img_key = key
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            self._pad_img = pygame.transform.smoothscale(img, key)
            self._pad_img_key = key
            return self._pad_img
        except Exception:
            self._pad_img = None
            self._pad_img_key = key
            return None

    def _refresh_game_list(self):
        self.remapped = list_remapped_games(self.config, self.all_games)
        self.pick_candidates = [g for g in self.all_games if g.get("platform") in ("steam", "epic", "nsp")]
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
        """Handle pygame events. axis_nav: callable(delta) for stick nav."""
        for event in events:
            if event.type == pygame.QUIT:
                self.finished = True
                return True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._back()
                elif event.key in (pygame.K_UP,):
                    self._nav(-1)
                elif event.key in (pygame.K_DOWN,):
                    self._nav(1)
                elif event.key in (pygame.K_LEFT,) and self.mode == "editor":
                    self._nav_h(-1)
                elif event.key in (pygame.K_RIGHT,) and self.mode == "editor":
                    self._nav_h(1)
                elif event.key == pygame.K_RETURN:
                    self._confirm()
                elif event.key == pygame.K_DELETE and self.mode == "game_list":
                    self._remove_selected_game()
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1 or event.button == 6:
                    self._back()
                elif event.button == 0 or event.button == 7:
                    self._confirm()
                elif event.button == 2 and self.mode == "editor":
                    self._reset_slot()
                elif event.button == 3 and self.mode == "game_list":
                    self._remove_selected_game()
                elif event.button == 4 and self.mode == "editor":
                    self._nav_h(-1)
                elif event.button == 5 and self.mode == "editor":
                    self._nav_h(1)
            if event.type == pygame.JOYAXISMOTION and self.mode == "editor":
                if event.axis == 5 and event.value > 0.72:
                    if self._trig_arm_rt:
                        self.scroll_grid(1)
                        self._trig_arm_rt = False
                elif event.axis == 5 and event.value < 0.2:
                    self._trig_arm_rt = True
                if event.axis == 4 and event.value > 0.72:
                    if self._trig_arm_lt:
                        self.scroll_grid(-1)
                        self._trig_arm_lt = False
                elif event.axis == 4 and event.value < 0.2:
                    self._trig_arm_lt = True
            if event.type == pygame.JOYHATMOTION and event.hat == 0:
                if self.mode == "editor":
                    if event.value[0] < 0:
                        self._nav_h(-1)
                    elif event.value[0] > 0:
                        self._nav_h(1)
                    elif event.value[1] > 0:
                        self._nav(-1)
                    elif event.value[1] < 0:
                        self._nav(1)
                else:
                    if event.value[1] > 0:
                        self._nav(-1)
                    elif event.value[1] < 0:
                        self._nav(1)
        if axis_nav:
            axis_nav(self._nav)
        return self.finished

    # Группы для ←→ : плечи | лев. стик | d-pad | прав. стик | ABXY+аккорды | настройки
    _EDITOR_H_GROUPS = (
        [0, 1, 2, 9, 10, 11],
        [3, 4],
        [5, 6, 7, 8],
        [12, 13],
        list(range(14, 26)),
        [26, 27, 28, 29, 30],
    )

    def _editor_h_group(self, slot_index):
        for gi, group in enumerate(self._EDITOR_H_GROUPS):
            if slot_index in group:
                return gi, group
        return 0, [slot_index]

    def _nav_h(self, delta):
        if self.mode != "editor" or not self.slots:
            return
        gi, group = self._editor_h_group(self.slot_index)
        new_gi = (gi + delta) % len(self._EDITOR_H_GROUPS)
        new_group = self._EDITOR_H_GROUPS[new_gi]
        if self.slot_index in new_group:
            return
        self.slot_index = new_group[0]
        self._snap_grid_scroll()

    def _nav(self, delta):
        if self.mode == "game_list":
            if not self.remapped:
                return
            self.game_index = (self.game_index + delta) % len(self.remapped)
        elif self.mode == "pick_game":
            if not self.pick_candidates:
                return
            self.pick_index = (self.pick_index + delta) % len(self.pick_candidates)
        elif self.mode == "editor":
            n = len(self.slots)
            if n == 0:
                return
            self.slot_index = (self.slot_index + delta) % n
            self._snap_grid_scroll()

    def _grid_header_h(self):
        return 6 + self.font_list.get_linesize() + 6

    def _grid_max_scroll(self, areas):
        header_h = self._grid_header_h()
        visible = max(1, areas["grid_rows_h"] - header_h)
        face_line_h = areas["face_line_h"]
        _, indices = _grid_column_specs(self.slots)[FACE_COL_INDEX]
        n = sum(1 for idx in indices if idx is not None)
        return max(0, n * face_line_h - visible)

    def _slot_grid_pos(self, slot_index, areas):
        line_h = areas["line_h"]
        face_line_h = areas["face_line_h"]
        for col, (_, indices) in enumerate(_grid_column_specs(self.slots)):
            col_h = face_line_h if col == FACE_COL_INDEX else line_h
            row = 0
            for idx in indices:
                if idx is None:
                    continue
                if idx == slot_index:
                    return col, row, col_h
                row += col_h
        return None

    def _snap_grid_scroll(self, areas=None):
        if self.mode != "editor":
            return
        if areas is None:
            w, h = self.screen.get_size()
            areas = self._editor_areas(w, h)
        pos = self._slot_grid_pos(self.slot_index, areas)
        if pos is None:
            return
        col, rel_y, row_h = pos
        if col != FACE_COL_INDEX:
            return
        header_h = self._grid_header_h()
        visible = max(1, areas["grid_rows_h"] - header_h)
        max_scroll = self._grid_max_scroll(areas)
        if rel_y < self.scroll:
            self.scroll = rel_y
        elif rel_y + row_h > self.scroll + visible:
            self.scroll = rel_y + row_h - visible
        self.scroll = max(0, min(max_scroll, self.scroll))

    def scroll_grid(self, delta_pages):
        if self.mode != "editor":
            return
        w, h = self.screen.get_size()
        areas = self._editor_areas(w, h)
        step = max(areas["face_line_h"] * 3, 36)
        max_scroll = self._grid_max_scroll(areas)
        self.scroll = max(0, min(max_scroll, self.scroll + delta_pages * step))

    def _snap_scroll(self):
        if self.mode == "editor":
            return
        w, h = self.screen.get_size()
        line_h = self.font_list.get_linesize() + 6
        visible = max(1, (h - 280) // line_h)
        if self.slot_index < self.scroll:
            self.scroll = self.slot_index
        elif self.slot_index >= self.scroll + visible:
            self.scroll = self.slot_index - visible + 1

    def _confirm(self):
        if self.mode == "game_list":
            if not self.remapped:
                self.mode = "pick_game"
                self.pick_index = 0
                return
            self._load_editor_for_game(self.remapped[self.game_index])
        elif self.mode == "pick_game":
            if not self.pick_candidates:
                return
            game = self.pick_candidates[self.pick_index]
            pid = suggest_profile_id(game)
            assign_game_profile(self.config, game, pid, self.base_dir)
            self.save_config(self.config)
            self._refresh_game_list()
            self._load_editor_for_game(game)
        elif self.mode == "editor":
            self._cycle_current_slot()

    def _back(self):
        if self.mode == "editor":
            save_profile(self.profile_path, self.profile)
            self.mode = "game_list"
            self._refresh_game_list()
        elif self.mode == "pick_game":
            self.mode = "game_list"
        else:
            self.finished = True

    def _remove_selected_game(self):
        if self.mode != "game_list" or not self.remapped:
            return
        unassign_game(self.config, self.remapped[self.game_index])
        self.save_config(self.config)
        self._refresh_game_list()

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
        w, h = self.screen.get_size()
        self.screen.fill(self.bg)
        if self.mode == "game_list":
            self._draw_game_list(w, h)
        elif self.mode == "pick_game":
            self._draw_pick_game(w, h)
        else:
            self._draw_editor(w, h)

    def _draw_header(self, title, hint, w):
        surf = self.font_title.render(title, True, self.title)
        self.screen.blit(surf, ((w - surf.get_width()) // 2, 24))
        hint_s = self.font_hint.render(hint, True, self.title)
        self.screen.blit(hint_s, ((w - hint_s.get_width()) // 2, 24 + surf.get_height() + 8))

    def _draw_game_list(self, w, h):
        self._draw_header(
            "Controller mapping",
            "A: edit / add   B: back   X: remove game from list",
            w,
        )
        margin = max(40, w // 20)
        list_w = min(w - margin * 2, 900)
        list_x = (w - list_w) // 2
        y0 = self.font_title.get_linesize() + self.font_hint.get_linesize() + 48
        if not self.remapped:
            msg = self.font_list.render("No games yet — press A to add", True, self.text)
            self.screen.blit(msg, (list_x, y0))
            return
        line_h = self.font_list.get_linesize() + 10
        for i, g in enumerate(self.remapped):
            y = y0 + i * line_h
            if y > h - 80:
                break
            name = g.get("name") or game_remap_key(g)
            pid = get_assigned_profile_id(self.config, g)
            label = "%s  →  %s" % (name, pid)
            if i == self.game_index:
                pygame.draw.rect(self.screen, self.highlight, (list_x - 8, y - 4, list_w + 16, line_h - 2), 1)
            surf = self.font_list.render(label, True, self.text)
            self.screen.blit(surf, (list_x, y))

    def _draw_pick_game(self, w, h):
        self._draw_header("Add game", "A: assign mapping   B: cancel", w)
        margin = max(40, w // 20)
        list_w = min(w - margin * 2, 900)
        list_x = (w - list_w) // 2
        y0 = self.font_title.get_linesize() + self.font_hint.get_linesize() + 48
        line_h = self.font_list.get_linesize() + 8
        visible = max(1, (h - y0 - 60) // line_h)
        start = max(0, min(self.pick_index - visible // 2, len(self.pick_candidates) - visible))
        for row, gi in enumerate(range(start, min(len(self.pick_candidates), start + visible))):
            g = self.pick_candidates[gi]
            y = y0 + row * line_h
            sel = gi == self.pick_index
            if sel:
                pygame.draw.rect(self.screen, self.highlight, (list_x - 8, y - 4, list_w + 16, line_h - 2), 1)
            label = "%s (%s)" % (g.get("name", "?"), g.get("platform", "?"))
            surf = self.font_list.render(label, True, self.text)
            self.screen.blit(surf, (list_x, y))

    def _editor_areas(self, w, h):
        title_h = self.font_title.get_linesize()
        hint_h = self.font_hint.get_linesize()
        header_h = 20 + title_h + 6 + hint_h + 12
        footer_h = 36
        line_h = self.font_list.get_linesize() + 5
        face_line_h = self.font_list.get_linesize() + 2
        settings_band = line_h * 2 + 18
        body_h = h - header_h - footer_h
        pad_h = max(120, int(body_h * 0.41))
        grid_h = body_h - pad_h - 8
        grid_rows_h = max(100, grid_h - settings_band)
        margin = max(24, w // 40)
        content_w = min(w - margin * 2, 1180)
        content_x = (w - content_w) // 2
        grid_top = header_h + pad_h + 8
        return {
            "header_h": header_h,
            "pad_top": header_h,
            "pad_h": pad_h,
            "grid_top": grid_top,
            "grid_h": grid_h,
            "grid_rows_h": grid_rows_h,
            "settings_y": grid_top + grid_rows_h + 4,
            "line_h": line_h,
            "face_line_h": face_line_h,
            "footer_y": h - footer_h,
            "content_x": content_x,
            "content_w": content_w,
            "cx": w // 2,
            "cy": header_h + pad_h // 2,
        }

    def _draw_editor(self, w, h):
        game_name = (self.current_game or {}).get("name") or "Game"
        self._draw_header(
            "Controller mapping: %s" % game_name,
            "↑↓ element   ←→ group   LT/RT FACE scroll   A +/change   X −/clear   B back",
            w,
        )
        areas = self._editor_areas(w, h)
        img_h = int(areas["pad_h"] * 0.88)
        img_w = int(img_h * PAD_IMAGE_ASPECT)
        img_w = min(img_w, int(areas["content_w"] * 0.62))
        pad_img = self._get_gamepad_image(img_w, img_h)
        if pad_img:
            rect = pad_img.get_rect(center=(areas["cx"], areas["cy"]))
            self.screen.blit(pad_img, rect)
            self._draw_pad_highlight(areas["cx"], areas["cy"], img_w, img_h)
        else:
            bw = min(int(areas["pad_h"] * 1.55), int(areas["content_w"] * 0.34), 420)
            bh = int(areas["pad_h"] * 0.62)
            self._draw_controller_wireframe(areas["cx"], areas["cy"], bw, bh)
        self._draw_shoulder_panels(areas)
        self._draw_mapping_grid(areas)
        self._draw_editor_footer(w, areas["footer_y"])

    def _draw_pad_highlight(self, cx, cy, iw, ih):
        if not self.slots:
            return
        slot = self.slots[self.slot_index]
        hit = _pad_hotspot(slot)
        if not hit:
            return
        (nx, ny), rkey = hit
        px = cx - iw // 2 + int(nx * iw)
        py = cy - ih // 2 + int(ny * ih)
        r = max(10, int(iw * PAD_RADIUS.get(rkey, 0.045)))
        pygame.draw.circle(self.screen, self.highlight, (px, py), r + 4, 3)
        pygame.draw.circle(self.screen, self.highlight, (px, py), max(6, r - 6), 1)

    def _draw_controller_wireframe(self, cx, cy, bw, bh):
        o = OUTLINE_COLOR
        hw, hh = bw // 2, bh // 2
        body = pygame.Rect(cx - hw, cy - hh + hh // 5, bw, int(bh * 0.78))
        pygame.draw.ellipse(self.screen, o, body, 2)
        grip_l = pygame.Rect(cx - hw - int(bw * 0.08), cy - int(hh * 0.15), int(bw * 0.38), int(bh * 0.72))
        grip_r = pygame.Rect(cx + hw - int(bw * 0.30), cy - int(hh * 0.15), int(bw * 0.38), int(bh * 0.72))
        pygame.draw.ellipse(self.screen, o, grip_l, 2)
        pygame.draw.ellipse(self.screen, o, grip_r, 2)

        ls_x = cx - int(bw * 0.20)
        ls_y = cy + int(bh * 0.06)
        rs_x = cx + int(bw * 0.18)
        rs_y = cy + int(bh * 0.14)
        lr = max(16, int(bw * 0.09))
        rr = max(14, int(bw * 0.08))
        for x, y, r in ((ls_x, ls_y, lr), (rs_x, rs_y, rr)):
            pygame.draw.circle(self.screen, o, (x, y), r, 2)
            pygame.draw.circle(self.screen, o, (x, y), max(6, r - 8), 2)

        dp_x = cx - int(bw * 0.34)
        dp_y = cy + int(bh * 0.20)
        d = max(8, int(bw * 0.035))
        pygame.draw.rect(self.screen, o, (dp_x - d, dp_y - d * 3, d * 2, d * 2), 2)
        pygame.draw.rect(self.screen, o, (dp_x - d, dp_y + d, d * 2, d * 2), 2)
        pygame.draw.rect(self.screen, o, (dp_x - d * 3, dp_y - d, d * 2, d * 2), 2)
        pygame.draw.rect(self.screen, o, (dp_x + d, dp_y - d, d * 2, d * 2), 2)

        fx = cx + int(bw * 0.30)
        fy = cy + int(bh * 0.02)
        off = max(10, int(bw * 0.045))
        btn_r = max(8, int(bw * 0.038))
        for dx, dy in ((0, -off), (off, 0), (0, off), (-off, 0)):
            pygame.draw.circle(self.screen, o, (fx + dx, fy + dy), btn_r, 2)

        xb_y = cy - int(bh * 0.12)
        pygame.draw.circle(self.screen, o, (cx, xb_y), max(7, int(bw * 0.035)), 2)

        li = _slot_index(self.slots, "left_stick")
        ri = _slot_index(self.slots, "right_stick")
        if self.slot_index == li:
            pygame.draw.circle(self.screen, self.highlight, (ls_x, ls_y), lr + 4, 2)
        if self.slot_index == ri:
            pygame.draw.circle(self.screen, self.highlight, (rs_x, rs_y), rr + 4, 2)

    def _draw_shoulder_panels(self, areas):
        panel_w = max(176, min(210, int(areas["content_w"] * 0.16)))
        row_h = self.font_list.get_linesize() + self.font_hint.get_linesize() + 18
        left_x = areas["content_x"] + 6
        right_x = areas["content_x"] + areas["content_w"] - panel_w - 6
        top_y = areas["pad_top"] + 6
        bot_y = areas["pad_top"] + areas["pad_h"] - row_h - 8

        left_top = [
            ("Left bumper", _slot_index(self.slots, "button", str(BTN_LB)), "LB"),
            ("Left trigger", _slot_index(self.slots, "trigger", "left"), "LT"),
        ]
        right_top = [
            ("Right bumper", _slot_index(self.slots, "button", str(BTN_RB)), "RB"),
            ("Right trigger", _slot_index(self.slots, "trigger", "right"), "RT"),
        ]
        for i, (title, idx, badge) in enumerate(left_top):
            self._draw_shoulder_row(left_x, top_y + i * row_h, panel_w, row_h, title, idx, badge, "left")
        for i, (title, idx, badge) in enumerate(right_top):
            self._draw_shoulder_row(right_x, top_y + i * row_h, panel_w, row_h, title, idx, badge, "right")

        self._draw_shoulder_row(
            left_x, bot_y, panel_w, row_h, "Back",
            _slot_index(self.slots, "button", str(BTN_BACK)), "View", "left",
        )
        self._draw_shoulder_row(
            right_x, bot_y, panel_w, row_h, "Start",
            _slot_index(self.slots, "button", str(BTN_START)), "Menu", "right",
        )

    def _draw_shoulder_row(self, x, y, w, h, title, slot_i, badge, side):
        if slot_i is None:
            return
        slot = self.slots[slot_i]
        selected = slot_i == self.slot_index
        if selected:
            pygame.draw.rect(self.screen, PANEL_SEL, (x, y, w, h - 2), border_radius=6)
        pygame.draw.rect(self.screen, OUTLINE_COLOR if selected else (60, 64, 78), (x, y, w, h - 2), 1, border_radius=6)

        badge_s = self.font_hint.render(badge, True, self.title)
        badge_pad = 10

        if side == "left":
            badge_x = x + w - badge_pad - badge_s.get_width()
            text_right = badge_x - 8
            text_left = x + badge_pad
            text_w = max(20, text_right - text_left)
        else:
            badge_x = x + badge_pad
            text_left = badge_x + badge_s.get_width() + 8
            text_right = x + w - badge_pad
            text_w = max(20, text_right - text_left)

        title_txt = _truncate_text(self.font_list, title, text_w)
        title_s = self.font_list.render(title_txt, True, self.text if not selected else self.highlight)
        val_txt = _truncate_text(self.font_hint, _slot_display(slot), text_w)
        val_s = self.font_hint.render(val_txt, True, self.title)

        if side == "left":
            title_x = text_left
            val_x = text_left
        else:
            title_x = text_right - title_s.get_width()
            val_x = text_right - val_s.get_width()

        self.screen.blit(badge_s, (badge_x, y + 8))
        self.screen.blit(title_s, (title_x, y + 8))
        self.screen.blit(val_s, (val_x, y + h - val_s.get_height() - 10))

    def _draw_mapping_grid(self, areas):
        x0 = areas["content_x"]
        w = areas["content_w"]
        y = areas["grid_top"]
        line_h = areas["line_h"]
        face_line_h = areas["face_line_h"]
        col_w = w // 4
        row_inner = col_w - 28
        header_h = self._grid_header_h()
        list_top = y + header_h
        list_bottom = y + areas["grid_rows_h"]

        self._snap_grid_scroll(areas)

        columns = _grid_column_specs(self.slots)
        face_labels = {str(BTN_A): "A", str(BTN_B): "B", str(BTN_X): "X", str(BTN_Y): "Y"}
        dpad_short = {
            "dpad_up": "Up",
            "dpad_down": "Down",
            "dpad_left": "Left",
            "dpad_right": "Right",
        }

        pygame.draw.line(self.screen, OUTLINE_COLOR, (x0, y), (x0 + w, y), 1)

        for col, (header, _) in enumerate(columns):
            cx = x0 + col * col_w + 12
            hdr = self.font_list.render(header, True, self.title)
            self.screen.blit(hdr, (cx, y + 6))

        def _draw_column(col, indices, scroll_offset=0, clip=None):
            cx = x0 + col * col_w + 12
            col_line_h = face_line_h if col == FACE_COL_INDEX else line_h
            prev_clip = None
            if clip is not None:
                prev_clip = self.screen.get_clip()
                self.screen.set_clip(clip)
            rel_y = 0
            for idx in indices:
                if idx is None:
                    continue
                draw_y = list_top + rel_y - scroll_offset
                if draw_y + col_line_h > list_top and draw_y < list_bottom:
                    slot = self.slots[idx]
                    if slot["kind"] == "dpad":
                        label = dpad_short.get(slot["key"], slot["label"])
                    elif slot["kind"] == "stick_click":
                        label = slot["label"]
                    elif slot["kind"] == "chord":
                        label = slot["label"].replace("Button ", "")
                    elif slot["kind"] == "button" and slot["key"] in face_labels:
                        label = face_labels[slot["key"]]
                    else:
                        label = slot["label"]
                    color = None
                    if slot["kind"] == "button" and slot["key"] in face_labels:
                        color = FACE_BTN_COLORS.get(slot["key"])
                    elif slot["kind"] == "chord" and slot.get("key", "").startswith(("lb_", "rb_")):
                        color = (120, 130, 150)
                    self._draw_grid_row(cx, draw_y, row_inner, col_line_h, label, idx, color)
                rel_y += col_line_h
            if clip is not None:
                self.screen.set_clip(prev_clip)

        for col in range(FACE_COL_INDEX):
            _, indices = columns[col]
            _draw_column(col, indices)

        face_x = x0 + FACE_COL_INDEX * col_w
        face_clip = pygame.Rect(face_x, list_top, col_w, max(1, list_bottom - list_top))
        _, face_indices = columns[FACE_COL_INDEX]
        _draw_column(FACE_COL_INDEX, face_indices, scroll_offset=self.scroll, clip=face_clip)

        settings_y = areas["settings_y"]
        pygame.draw.line(self.screen, OUTLINE_COLOR, (x0, settings_y - 6), (x0 + w, settings_y - 6), 1)
        ms = _slot_index(self.slots, "mouse_sens")
        msc = _slot_index(self.slots, "mouse_scale")
        dz = _slot_index(self.slots, "deadzone")
        ma = _slot_index(self.slots, "mouse_accel")
        maolt = _slot_index(self.slots, "mouse_accel_off_lt")
        setting_w = w // 3 - 24
        setting_w2 = w // 2 - 24
        settings_row2_y = settings_y + line_h + 6
        if ms is not None:
            self._draw_grid_row(x0 + 12, settings_y, setting_w, line_h, "Mouse speed", ms)
        if msc is not None:
            self._draw_grid_row(x0 + w // 3 + 12, settings_y, setting_w, line_h, "Mouse scale", msc)
        if dz is not None:
            self._draw_grid_row(x0 + 2 * w // 3 + 12, settings_y, setting_w, line_h, "Deadzone", dz)
        if ma is not None:
            self._draw_grid_row(x0 + 12, settings_row2_y, setting_w2, line_h, "Mouse accel", ma)
        if maolt is not None:
            self._draw_grid_row(
                x0 + w // 2 + 12, settings_row2_y, setting_w2, line_h, "Accel off LT", maolt
            )

    def _draw_grid_row(self, x, y, w, h, label, slot_i, badge_color=None):
        slot = self.slots[slot_i]
        selected = slot_i == self.slot_index
        if selected:
            pygame.draw.rect(self.screen, PANEL_SEL, (x - 4, y - 2, w + 8, h + 2), border_radius=4)

        lx = x + (22 if badge_color else 0)
        inner_w = w - (22 if badge_color else 0)
        if badge_color:
            pygame.draw.circle(self.screen, badge_color, (x + 9, y + h // 2), 7)

        label_s = self.font_list.render(
            _truncate_text(self.font_list, label, inner_w // 2),
            True,
            self.text if not selected else self.highlight,
        )
        val_s = self.font_list.render(
            _slot_display(slot),
            True,
            self.highlight if selected else self.title,
        )
        val_x = x + w - val_s.get_width()
        label_max = max(20, val_x - lx - 10)
        if label_s.get_width() > label_max:
            label_s = self.font_list.render(
                _truncate_text(self.font_list, label, label_max),
                True,
                self.text if not selected else self.highlight,
            )
        self.screen.blit(label_s, (lx, y + 1))
        self.screen.blit(val_s, (val_x, y + 1))

    def _draw_editor_footer(self, w, y):
        hints = [
            ("A", "Select / +", (107, 191, 89)),
            ("X", "Clear / −", (191, 176, 77)),
            ("B", "Back", (191, 77, 77)),
        ]
        x = w // 2 - 180
        for key, action, col in hints:
            ks = self.font_hint.render(key, True, col)
            self.screen.blit(ks, (x, y + 8))
            x += ks.get_width() + 4
            act = self.font_hint.render(action, True, self.title)
            self.screen.blit(act, (x, y + 8))
            x += act.get_width() + 24
