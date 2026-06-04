"""Tests for XInput stick normalization helpers."""

from joypad.input.xinput import apply_deadzone, norm_axis


def test_norm_axis_clamps():
    assert norm_axis(32768) == 1.0
    assert norm_axis(-32768) == -1.0
    assert norm_axis(0) == 0.0


def test_apply_deadzone_zeros_small_values():
    assert apply_deadzone(0.05, 0.1) == 0.0


def test_apply_deadzone_scales_outside_deadzone():
    v = apply_deadzone(0.5, 0.1)
    assert v > 0.4
