"""Profile key string parsing."""

from joypad.input.constants import (
    _BTN_PROFILE_ALIASES,
    _FACE_PROFILE_ALIASES,
    BTN_FACE,
)


def parse_profile_btn_key(key):
    """Profile key -> internal index string ('0'–'7'). Accepts a/b/x/y/lb/rb/back/start."""
    if key is None:
        return None
    alias = str(key).strip().lower()
    idx = _BTN_PROFILE_ALIASES.get(alias)
    return str(idx) if idx is not None else alias


def parse_profile_face_key(key):
    """Chord face key -> internal index string ('0'–'3'). Accepts a/b/x/y."""
    if key is None:
        return None
    alias = str(key).strip().lower()
    idx = _FACE_PROFILE_ALIASES.get(alias)
    return str(idx) if idx is not None else alias


def parse_chord_slot_key(key):
    """'lb_0' -> ('lb', '0') or None."""
    if not key or "_" not in key:
        return None
    mod, face = key.split("_", 1)
    if mod in ("lb", "rb") and face in {str(i) for i in BTN_FACE}:
        return mod, face
    return None
