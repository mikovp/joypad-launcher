"""Stick-to-keyboard and mouse acceleration helpers."""

import math

from joypad.input.bindings import VK


def apply_stick_keys(set_key_level, mode, deadzone, lx, ly):
    if mode == "wasd":
        set_key_level(VK["w"], ly > deadzone)
        set_key_level(VK["s"], ly < -deadzone)
        set_key_level(VK["a"], lx < -deadzone)
        set_key_level(VK["d"], lx > deadzone)
    elif mode == "arrows":
        set_key_level(0x26, ly > deadzone)
        set_key_level(0x28, ly < -deadzone)
        set_key_level(0x25, lx < -deadzone)
        set_key_level(0x27, lx > deadzone)


def clear_stick_keys(set_key_level):
    for vk in (VK["w"], VK["a"], VK["s"], VK["d"], 0x25, 0x26, 0x27, 0x28):
        set_key_level(vk, False)


def mouse_accel_multiplier(mouse_accel, mouse_accel_off_lt, rx, ry, lt_pressed):
    if mouse_accel <= 0:
        return 1.0
    if mouse_accel_off_lt and lt_pressed:
        return 1.0
    mag = min(1.0, math.hypot(rx, ry))
    return 1.0 + mouse_accel * (mag * mag)
