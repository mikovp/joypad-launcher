from joypad.input.constants import STICK_MODES, RIGHT_STICK_MODES


def _build_keyboard_bindings():
    """Profile binding ids → Windows VK codes; labels for the editor cycle list."""
    rows = [
        ("space", 0x20, "Space"),
        ("enter", 0x0D, "Enter"),
        ("escape", 0x1B, "Esc"),
        ("tab", 0x09, "Tab"),
        ("backspace", 0x08, "Backspace"),
        ("delete", 0x2E, "Delete"),
        ("shift", 0x10, "Shift"),
        ("ctrl", 0x11, "Ctrl"),
        ("alt", 0x12, "Alt"),
        ("arrow_up", 0x26, "↑"),
        ("arrow_down", 0x28, "↓"),
        ("arrow_left", 0x25, "←"),
        ("arrow_right", 0x27, "→"),
        ("home", 0x24, "Home"),
        ("end", 0x23, "End"),
        ("pageup", 0x21, "PgUp"),
        ("pagedown", 0x22, "PgDn"),
    ]
    for i in range(1, 13):
        rows.append(("f%d" % i, 0x70 + i - 1, "F%d" % i))
    for ch in "abcdefghijklmnopqrstuvwxyz":
        rows.append((ch, ord(ch.upper()), ch.upper()))
    for ch in "0123456789":
        rows.append((ch, ord(ch), ch))
    vk = {bid: code for bid, code, _label in rows}
    editor = [(bid, label) for bid, _code, label in rows]
    return vk, editor


VK, _KEYBOARD_BINDINGS = _build_keyboard_bindings()

BUTTON_BINDINGS = [
    ("none", "—"),
    ("mouse_left", "LMB"),
    ("mouse_right", "RMB"),
    ("mouse_middle", "MMB"),
    ("mouse_wheel_up", "Wheel ↑"),
    ("mouse_wheel_down", "Wheel ↓"),
] + _KEYBOARD_BINDINGS

DPAD_BINDINGS = [
    ("dpad_up", "D-Up"),
    ("dpad_down", "D-Down"),
    ("dpad_left", "D-Left"),
    ("dpad_right", "D-Right"),
]


def binding_label(binding_id):
    for bid, label in BUTTON_BINDINGS:
        if bid == binding_id:
            return label
    return binding_id or "—"


def cycle_binding(current, bindings=None):
    bindings = bindings or BUTTON_BINDINGS
    ids = [b[0] for b in bindings]
    if current not in ids:
        return ids[0]
    idx = ids.index(current)
    return ids[(idx + 1) % len(ids)]


def cycle_stick_mode(current, modes=None):
    modes = modes or STICK_MODES
    if current not in modes:
        return modes[0]
    return modes[(modes.index(current) + 1) % len(modes)]


def cycle_right_stick_mode(current):
    return cycle_stick_mode(current, RIGHT_STICK_MODES)
