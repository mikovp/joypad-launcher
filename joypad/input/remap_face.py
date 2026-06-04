"""Face button and chord binding resolution."""

from joypad.input.constants import BTN_FACE, BTN_LB, BTN_RB, XINPUT_FACE
from joypad.input.profiles import ensure_chords


def resolve_face_bindings(profile, pad):
    """Map pressed face buttons to bindings, accounting for LB/RB chord layers."""
    buttons = profile.get("buttons") or {}
    chords = ensure_chords(profile)
    lb_held = bool(pad.wButtons & XINPUT_FACE[BTN_LB])
    rb_held = bool(pad.wButtons & XINPUT_FACE[BTN_RB])
    lb_chord_active = False
    rb_chord_active = False
    resolved = {}

    for btn_idx in BTN_FACE:
        face_key = str(btn_idx)
        pressed = bool(pad.wButtons & XINPUT_FACE[btn_idx])
        if not pressed:
            resolved[btn_idx] = (buttons.get(face_key, "none"), False)
            continue

        binding = None
        if lb_held:
            chord = (chords.get("lb") or {}).get(face_key, "none")
            if chord and chord != "none":
                binding = chord
                lb_chord_active = True
        if binding is None and rb_held:
            chord = (chords.get("rb") or {}).get(face_key, "none")
            if chord and chord != "none":
                binding = chord
                rb_chord_active = True
        if binding is None:
            binding = buttons.get(face_key, "none")
        resolved[btn_idx] = (binding, True)

    return resolved, lb_chord_active, rb_chord_active
