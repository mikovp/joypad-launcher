"""Pad hotspot lookup and mapping grid column layout."""

from joypad.input.bindings import DPAD_BINDINGS
from joypad.input.constants import BTN_A, BTN_B, BTN_BACK, BTN_LB, BTN_RB, BTN_START, BTN_X, BTN_Y
from joypad.input.profiles import parse_chord_slot_key
from joypad.ui.editor.slots.constants import _FACE_POINTS, PAD_LAYOUT


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
        if key in _FACE_POINTS:
            return _FACE_POINTS[key], "face"
    if kind == "chord":
        parsed = parse_chord_slot_key(key)
        if parsed:
            _, face = parsed
            pt = _FACE_POINTS.get(face)
            if pt:
                return pt, "face"
    return None


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
