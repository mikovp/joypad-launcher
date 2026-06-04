PROFILES_DIR_DEFAULT = "input_profiles"
DEFAULT_PROFILE_ID = "default_wasd_mouse"
TRIGGER_THRESHOLD = 30
GAME_WATCH_GRACE = 25.0
GAME_WATCH_ACTIVITY_GRACE = 15.0

# Xbox face buttons (match launcher.py BTN_* indices)
BTN_A = 0
BTN_B = 1
BTN_X = 2
BTN_Y = 3
BTN_LB = 4
BTN_RB = 5
BTN_BACK = 6
BTN_START = 7

STICK_MODES = ["none", "wasd", "arrows"]
RIGHT_STICK_MODES = ["none", "mouse"]
SLOT_BINDING_MODES = ("hold", "toggle")

BTN_FACE = (BTN_A, BTN_B, BTN_X, BTN_Y)

# Human-readable keys in profile JSON (also accept legacy "0"–"7").
BTN_PROFILE_NAMES = {
    BTN_A: "a",
    BTN_B: "b",
    BTN_X: "x",
    BTN_Y: "y",
    BTN_LB: "lb",
    BTN_RB: "rb",
    BTN_BACK: "back",
    BTN_START: "start",
}
FACE_PROFILE_NAMES = {BTN_A: "a", BTN_B: "b", BTN_X: "x", BTN_Y: "y"}

_BTN_PROFILE_ALIASES = {}
for _idx, _name in BTN_PROFILE_NAMES.items():
    _BTN_PROFILE_ALIASES[_name] = _idx
    _BTN_PROFILE_ALIASES[str(_idx)] = _idx

_FACE_PROFILE_ALIASES = {}
for _idx, _name in FACE_PROFILE_NAMES.items():
    _FACE_PROFILE_ALIASES[_name] = _idx
    _FACE_PROFILE_ALIASES[str(_idx)] = _idx

XINPUT_DPAD = {
    "dpad_up": 0x0001,
    "dpad_down": 0x0002,
    "dpad_left": 0x0004,
    "dpad_right": 0x0008,
}

XINPUT_FACE = {
    BTN_A: 0x1000,
    BTN_B: 0x2000,
    BTN_X: 0x4000,
    BTN_Y: 0x8000,
    BTN_LB: 0x0100,
    BTN_RB: 0x0200,
    BTN_BACK: 0x0020,
    BTN_START: 0x0010,
}
