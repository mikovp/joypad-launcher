"""Editor slot layout constants and navigation order."""

from joypad.input.constants import (
    BTN_A,
    BTN_B,
    BTN_BACK,
    BTN_LB,
    BTN_RB,
    BTN_START,
    BTN_X,
    BTN_Y,
)

BTN_LAYOUT = [
    ("btn_%d" % BTN_A, "A", BTN_A),
    ("btn_%d" % BTN_B, "B", BTN_B),
    ("btn_%d" % BTN_X, "X", BTN_X),
    ("btn_%d" % BTN_Y, "Y", BTN_Y),
    ("btn_%d" % BTN_LB, "LB", BTN_LB),
    ("btn_%d" % BTN_RB, "RB", BTN_RB),
    ("btn_%d" % BTN_BACK, "Back", BTN_BACK),
    ("btn_%d" % BTN_START, "Start", BTN_START),
]

STICK_MODE_LABELS = {
    "none": "—",
    "wasd": "WASD",
    "arrows": "Arrows",
    "mouse": "Mouse",
}


def _face_nav_entries():
    face = [
        (BTN_A, "A"),
        (BTN_B, "B"),
        (BTN_X, "X"),
        (BTN_Y, "Y"),
    ]
    entries = []
    for idx, short in face:
        entries.append(("button", str(idx), short))
        entries.append(("chord", "lb_%d" % idx, "LB + %s" % short))
        entries.append(("chord", "rb_%d" % idx, "RB + %s" % short))
    return entries


EDITOR_NAV_ORDER = [
    ("button", str(BTN_LB), "Left bumper"),
    ("trigger", "left", "Left trigger"),
    ("button", str(BTN_BACK), "Back"),
    ("left_stick", None, "Joystick"),
    ("stick_click", "left", "L-stick click"),
    ("dpad", "dpad_up", "D-Up"),
    ("dpad", "dpad_down", "D-Down"),
    ("dpad", "dpad_left", "D-Left"),
    ("dpad", "dpad_right", "D-Right"),
    ("button", str(BTN_RB), "Right bumper"),
    ("trigger", "right", "Right trigger"),
    ("button", str(BTN_START), "Start"),
    ("right_stick", None, "Joystick"),
    ("stick_click", "right", "R-stick click"),
] + _face_nav_entries() + [
    ("mouse_sens", None, "Mouse speed"),
    ("mouse_scale", None, "Mouse scale"),
    ("deadzone", None, "Deadzone"),
    ("mouse_accel", None, "Mouse accel"),
    ("mouse_accel_off_lt", None, "Accel off LT"),
]

NUMERIC_SLOT_KINDS = ("mouse_sens", "mouse_scale", "deadzone", "mouse_accel")
NUMERIC_SLOT_STEPS = {
    "mouse_sens": ("mouse_sensitivity", 0.1, 0.1, 50.0),
    "mouse_scale": ("mouse_scale", 0.1, 0.1, 10.0),
    "deadzone": ("deadzone", 0.01, 0.0, 1.0),
    "mouse_accel": ("mouse_acceleration", 0.05, 0.0, 2.0),
}
BOOL_SLOT_KINDS = ("mouse_accel_off_lt",)

FACE_BTN_COLORS = {
    str(BTN_A): (107, 191, 89),
    str(BTN_B): (191, 77, 77),
    str(BTN_X): (77, 130, 191),
    str(BTN_Y): (191, 176, 77),
}

OUTLINE_COLOR = (150, 156, 170)
PAD_IMAGE_FILE = "xbox-controller-clipart-md.png"
PAD_IMAGE_ASPECT = 800 / 549
_FACE_POINTS: dict[str, tuple[float, float]] = {
    str(BTN_A): (0.752, 0.379),
    str(BTN_B): (0.822, 0.285),
    str(BTN_X): (0.682, 0.280),
    str(BTN_Y): (0.752, 0.181),
}
PAD_LAYOUT = {
    "ls": (0.244, 0.415),
    "rs": (0.618, 0.664),
    "dpad": (0.378, 0.660),
    "lb": (0.231, 0.121),
    "rb": (0.767, 0.121),
    "lt": (0.251, 0.054),
    "rt": (0.748, 0.054),
    "back": (0.395, 0.415),
    "start": (0.600, 0.416),
    "face": _FACE_POINTS,
}
PAD_RADIUS = {
    "stick": 0.048,
    "stick_click": 0.040,
    "face": 0.040,
    "dpad": 0.052,
    "shoulder": 0.050,
    "trigger": 0.046,
    "center": 0.030,
}
PANEL_FILL = (32, 35, 46)
PANEL_SEL = (55, 62, 82)
FACE_COL_INDEX = 3
