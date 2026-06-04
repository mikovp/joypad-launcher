"""Build editor slots and mutate profile values."""

from joypad.input.bindings import cycle_binding, cycle_right_stick_mode, cycle_stick_mode
from joypad.input.profiles import (
    ensure_chords,
    format_slot_binding,
    parse_chord_slot_key,
    parse_slot_binding,
)
from joypad.ui.editor.slots.constants import (
    EDITOR_NAV_ORDER,
    NUMERIC_SLOT_STEPS,
)


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
