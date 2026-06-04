"""No-op XInput stubs for non-Windows platforms."""


def read_xinput(user_index=0):
    return None


def gamepad_active(pad, threshold=8000):
    return False


def scan_xinput_indices():
    return []


def pick_xinput_index(preferred=0):
    return preferred

_xinput = None
