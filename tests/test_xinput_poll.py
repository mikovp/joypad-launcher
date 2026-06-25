"""Tests for XInput-based launcher gamepad polling."""

from types import SimpleNamespace

from joypad.input.constants import BTN_A, BTN_B, XINPUT_FACE
from joypad.ui.loop.context import LoopContext
from joypad.ui.loop.xinput_poll import poll_xinput_input


class _FakePad:
    def __init__(self, w_buttons=0, sThumbLX=0, sThumbLY=0, bLeftTrigger=0, bRightTrigger=0):
        self.wButtons = w_buttons
        self.sThumbLX = sThumbLX
        self.sThumbLY = sThumbLY
        self.bLeftTrigger = bLeftTrigger
        self.bRightTrigger = bRightTrigger


def test_poll_xinput_b_opens_system_menu(monkeypatch):
    state = SimpleNamespace(overlay_menu=None, input_remap_session=None)
    ctx = LoopContext()
    sequence = [_FakePad(), _FakePad(w_buttons=XINPUT_FACE[BTN_B])]

    monkeypatch.setattr(
        "joypad.ui.loop.xinput_poll.read_xinput",
        lambda _index=0: sequence.pop(0) if sequence else _FakePad(),
    )
    monkeypatch.setattr("joypad.ui.loop.xinput_poll.pick_xinput_index", lambda _preferred=0: 0)

    assert poll_xinput_input(state, ctx, on_launch=lambda: False) is False
    assert poll_xinput_input(state, ctx, on_launch=lambda: False) is False
    assert state.overlay_menu == "system"


def test_poll_xinput_a_launches_when_on_launch_true(monkeypatch):
    state = SimpleNamespace(overlay_menu=None, input_remap_session=None)
    ctx = LoopContext()
    sequence = [_FakePad(), _FakePad(w_buttons=XINPUT_FACE[BTN_A])]

    monkeypatch.setattr(
        "joypad.ui.loop.xinput_poll.read_xinput",
        lambda _index=0: sequence.pop(0) if sequence else _FakePad(),
    )
    monkeypatch.setattr("joypad.ui.loop.xinput_poll.pick_xinput_index", lambda _preferred=0: 0)

    poll_xinput_input(state, ctx, on_launch=lambda: False)
    assert poll_xinput_input(state, ctx, on_launch=lambda: True) is True
