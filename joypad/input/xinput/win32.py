"""Windows XInput polling."""

from ctypes import Structure, byref, c_short, c_ubyte, windll
from ctypes.wintypes import DWORD, WORD

from joypad.input.constants import TRIGGER_THRESHOLD
from joypad.input.log import remap_log


class XINPUT_GAMEPAD(Structure):
    _fields_ = [
        ("wButtons", WORD),
        ("bLeftTrigger", c_ubyte),
        ("bRightTrigger", c_ubyte),
        ("sThumbLX", c_short),
        ("sThumbLY", c_short),
        ("sThumbRX", c_short),
        ("sThumbRY", c_short),
    ]


class XINPUT_STATE(Structure):
    _fields_ = [("dwPacketNumber", DWORD), ("Gamepad", XINPUT_GAMEPAD)]


_xinput = None
for _dll in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
    try:
        _xinput = windll.LoadLibrary(_dll)
        break
    except OSError:
        pass


def read_xinput(user_index=0):
    if not _xinput:
        return None
    state = XINPUT_STATE()
    if _xinput.XInputGetState(user_index, byref(state)) != 0:
        return None
    return state.Gamepad


def gamepad_active(pad, threshold=8000):
    if pad is None:
        return False
    if pad.wButtons:
        return True
    if pad.bLeftTrigger >= TRIGGER_THRESHOLD or pad.bRightTrigger >= TRIGGER_THRESHOLD:
        return True
    for axis in (pad.sThumbLX, pad.sThumbLY, pad.sThumbRX, pad.sThumbRY):
        if abs(int(axis)) > threshold:
            return True
    return False


def scan_xinput_indices():
    found: list[tuple[int, int, int, int]] = []
    if not _xinput:
        return found
    for i in range(4):
        state = XINPUT_STATE()
        if _xinput.XInputGetState(i, byref(state)) == 0:
            gp = state.Gamepad
            found.append((i, gp.wButtons, gp.sThumbLX, gp.sThumbLY))
    return found


def pick_xinput_index(preferred=0):
    connected = scan_xinput_indices()
    if not connected:
        return preferred
    indices = [c[0] for c in connected]
    if preferred in indices:
        return preferred
    remap_log("auto-selected XInput index %s (preferred %s unavailable)" % (indices[0], preferred))
    return indices[0]
