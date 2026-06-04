import json
import os

from joypad.ui.editor.slots import build_editor_slots

PROFILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "input_profiles",
    "default_wasd_mouse.json",
)


def test_build_editor_slots_from_default_profile():
    with open(PROFILE, encoding="utf-8") as f:
        profile = json.load(f)
    slots = build_editor_slots(profile)
    assert len(slots) > 0
    kinds = {s["kind"] for s in slots}
    assert "left_stick" in kinds
    assert "button" in kinds
