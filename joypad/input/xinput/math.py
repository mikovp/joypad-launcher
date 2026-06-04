"""Stick axis normalization."""

XINPUT_L3 = 0x0040
XINPUT_R3 = 0x0080


def norm_axis(v):
    return max(-1.0, min(1.0, v / 32768.0))


def apply_deadzone(v, deadzone):
    if abs(v) < deadzone:
        return 0.0
    sign = 1.0 if v > 0 else -1.0
    return sign * (abs(v) - deadzone) / (1.0 - deadzone)
