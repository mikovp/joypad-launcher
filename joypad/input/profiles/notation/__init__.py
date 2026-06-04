"""Profile key normalization and readable JSON notation."""

from joypad.input.profiles.notation.chords import default_chords, ensure_chords
from joypad.input.profiles.notation.format import format_profile_notation
from joypad.input.profiles.notation.keys import (
    parse_chord_slot_key,
    parse_profile_btn_key,
    parse_profile_face_key,
)
from joypad.input.profiles.notation.normalize import normalize_profile_notation

__all__ = [
    "default_chords",
    "ensure_chords",
    "format_profile_notation",
    "normalize_profile_notation",
    "parse_chord_slot_key",
    "parse_profile_btn_key",
    "parse_profile_face_key",
]
