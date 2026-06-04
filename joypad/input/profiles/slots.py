"""Binding slot parse/format helpers."""

from joypad.input.constants import SLOT_BINDING_MODES


def parse_slot_binding(value, default_mode="hold"):
    """Parse a binding slot: string or {binding, mode}. mode: hold | toggle."""
    if isinstance(value, dict):
        binding = value.get("binding") or value.get("bind") or "none"
        mode = str(value.get("mode") or default_mode).lower()
        if mode not in SLOT_BINDING_MODES:
            mode = default_mode
        return binding, mode
    if not value:
        return "none", default_mode
    return str(value), default_mode


def format_slot_binding(binding, mode="hold"):
    """Serialize binding for profile JSON (object when mode is toggle)."""
    if mode == "toggle":
        return {"binding": binding, "mode": "toggle"}
    return binding


def normalize_stick_clicks(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        binding, mode = parse_slot_binding(value)
        if mode == "toggle":
            out[key] = {"binding": binding, "mode": "toggle"}
        else:
            out[key] = binding
    return out


def format_stick_clicks(section):
    if not section:
        return {}
    out = {}
    for key in ("left", "right"):
        if key not in section:
            continue
        binding, mode = parse_slot_binding(section[key])
        out[key] = format_slot_binding(binding, mode)
    for key, value in section.items():
        if key not in out:
            binding, mode = parse_slot_binding(value)
            out[key] = format_slot_binding(binding, mode)
    return out
