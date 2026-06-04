"""Normalize readable profile keys to internal numeric indices."""

import copy

from joypad.input.profiles.notation.chords import default_chords
from joypad.input.profiles.notation.keys import parse_profile_btn_key, parse_profile_face_key
from joypad.input.profiles.slots import normalize_stick_clicks


def normalize_button_map(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        norm = parse_profile_btn_key(key)
        if norm is not None:
            out[norm] = value
    return out


def normalize_button_holds(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        norm = parse_profile_btn_key(key)
        if norm is not None and isinstance(value, dict):
            out[norm] = value
    return out


def normalize_chords_map(chords):
    if not chords:
        return default_chords()
    out = {}
    for mod in ("lb", "rb"):
        layer = chords.get(mod) or {}
        out[mod] = {}
        for key, value in layer.items():
            norm = parse_profile_face_key(key)
            if norm is not None:
                out[mod][norm] = value
    return out


def normalize_profile_notation(profile):
    """Convert readable profile keys to internal numeric indices."""
    if not profile:
        return profile
    out = copy.deepcopy(profile)
    if "buttons" in out:
        out["buttons"] = normalize_button_map(out["buttons"])
    if "button_holds" in out:
        out["button_holds"] = normalize_button_holds(out["button_holds"])
    if "chords" in out:
        out["chords"] = normalize_chords_map(out["chords"])
    if "stick_clicks" in out:
        out["stick_clicks"] = normalize_stick_clicks(out["stick_clicks"])
    return out
