"""Format internal profile keys to readable JSON notation."""

import copy

from joypad.input.constants import (
    BTN_A,
    BTN_B,
    BTN_BACK,
    BTN_FACE,
    BTN_LB,
    BTN_PROFILE_NAMES,
    BTN_RB,
    BTN_START,
    BTN_X,
    BTN_Y,
    FACE_PROFILE_NAMES,
)
from joypad.input.profiles.notation.chords import default_chords
from joypad.input.profiles.slots import format_stick_clicks


def format_button_map(section):
    if not section:
        return {}
    order = (BTN_A, BTN_B, BTN_X, BTN_Y, BTN_LB, BTN_RB, BTN_BACK, BTN_START)
    out = {}
    for idx in order:
        key = str(idx)
        if key in section:
            out[BTN_PROFILE_NAMES[idx]] = section[key]
    for key, value in section.items():
        try:
            idx = int(key)
        except (TypeError, ValueError):
            out[str(key)] = value
            continue
        name = BTN_PROFILE_NAMES.get(idx)
        if name and name not in out:
            out[name] = value
    return out


def format_button_holds(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        try:
            idx = int(key)
            out[BTN_PROFILE_NAMES.get(idx, key)] = value
        except (TypeError, ValueError):
            out[str(key)] = value
    return out


def format_chords_map(chords):
    chords = chords or default_chords()
    out = {}
    for mod in ("lb", "rb"):
        layer = chords.get(mod) or {}
        out[mod] = {}
        for idx in BTN_FACE:
            key = str(idx)
            out[mod][FACE_PROFILE_NAMES[idx]] = layer.get(key, "none")
    return out


def format_profile_notation(profile):
    """Write profiles with readable button names (a, b, x, y, lb, …)."""
    out = copy.deepcopy(profile)
    if "buttons" in out:
        out["buttons"] = format_button_map(out["buttons"])
    if "button_holds" in out:
        out["button_holds"] = format_button_holds(out["button_holds"])
    if "chords" in out:
        out["chords"] = format_chords_map(out["chords"])
    if "stick_clicks" in out:
        out["stick_clicks"] = format_stick_clicks(out["stick_clicks"])
    return out
