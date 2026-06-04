"""Default chord layer structure."""

from joypad.input.constants import BTN_FACE


def default_chords():
    return {
        "lb": {str(i): "none" for i in BTN_FACE},
        "rb": {str(i): "none" for i in BTN_FACE},
    }


def ensure_chords(profile):
    chords = profile.setdefault("chords", default_chords())
    for mod in ("lb", "rb"):
        layer = chords.setdefault(mod, {})
        for i in BTN_FACE:
            layer.setdefault(str(i), "none")
    return chords
