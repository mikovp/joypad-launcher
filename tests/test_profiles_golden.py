import json
import os

from joypad.input import profiles as input_remap

PROFILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "input_profiles",
    "default_wasd_mouse.json",
)


def _load():
    with open(PROFILE, encoding="utf-8") as f:
        return json.load(f)


def test_normalize_then_format_round_trips_button_names():
    raw = _load()
    internal = input_remap.normalize_profile_notation(raw)
    assert internal["buttons"]["0"] == "space"   # a
    assert internal["buttons"]["1"] == "escape"  # b
    readable = input_remap.format_profile_notation(internal)
    assert readable["buttons"]["a"] == "space"
    assert readable["buttons"]["b"] == "escape"


def test_parse_profile_btn_key_aliases():
    assert input_remap.parse_profile_btn_key("a") == "0"
    assert input_remap.parse_profile_btn_key("start") == "7"
    assert input_remap.parse_profile_btn_key("3") == "3"


def test_parse_slot_binding_modes():
    assert input_remap.parse_slot_binding("space") == ("space", "hold")
    assert input_remap.parse_slot_binding(
        {"binding": "space", "mode": "toggle"}
    ) == ("space", "toggle")
    assert input_remap.parse_slot_binding(None) == ("none", "hold")


def test_default_chords_shape():
    ch = input_remap.default_chords()
    assert set(ch.keys()) == {"lb", "rb"}
    for mod in ("lb", "rb"):
        assert set(ch[mod].keys()) == {"0", "1", "2", "3"}
