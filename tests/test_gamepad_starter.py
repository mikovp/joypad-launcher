"""Tests for gamepad starter combo detection."""

from joypad.input.constants import BTN_BACK, BTN_START, XINPUT_FACE
from joypad.starter.combo import back_start_pressed, read_any_back_start


def test_back_start_pressed_requires_both():
    assert back_start_pressed(0) is False
    assert back_start_pressed(XINPUT_FACE[BTN_BACK]) is False
    assert back_start_pressed(XINPUT_FACE[BTN_START]) is False
    assert back_start_pressed(XINPUT_FACE[BTN_BACK] | XINPUT_FACE[BTN_START]) is True


def test_read_any_back_start_empty_indices():
    assert read_any_back_start([]) is False


def test_wait_for_combo_press_on_simultaneous_edge(monkeypatch):
    from joypad.starter import run as starter_run
    from joypad.starter.combo import GamepadScan

    sequence = iter([False, False, True, True])
    monkeypatch.setattr(starter_run, "read_any_back_start", lambda indices=None: next(sequence))
    monkeypatch.setattr(starter_run.time, "sleep", lambda _s: None)
    starter_run._wait_for_combo_press(10, 500, GamepadScan())
