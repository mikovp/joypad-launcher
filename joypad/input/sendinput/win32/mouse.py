"""Mouse injection via SendInput and SetCursorPos."""

from ctypes import byref, windll
from ctypes.wintypes import DWORD

from joypad.input.sendinput.win32 import structures as st
from joypad.input.sendinput.win32.core import send_input


def mouse_button(btn, down):
    flag_map = {
        "mouse_left": (st.MOUSEEVENTF_LEFTDOWN, st.MOUSEEVENTF_LEFTUP),
        "mouse_right": (st.MOUSEEVENTF_RIGHTDOWN, st.MOUSEEVENTF_RIGHTUP),
        "mouse_middle": (st.MOUSEEVENTF_MIDDLEDOWN, st.MOUSEEVENTF_MIDDLEUP),
    }
    pair = flag_map.get(btn)
    if not pair:
        return
    inp = st.INPUT(type=st.INPUT_MOUSE, u=st.INPUT_UNION(mi=st.MOUSEINPUT(0, 0, 0, pair[0 if down else 1], 0, 0)))
    send_input(inp)


def _mouse_move_sendinput(dx, dy):
    inp = st.INPUT(type=st.INPUT_MOUSE, u=st.INPUT_UNION(mi=st.MOUSEINPUT(int(dx), int(dy), 0, st.MOUSEEVENTF_MOVE, 0, 0)))
    return send_input(inp)


def _mouse_move_cursor(dx, dy):
    pt = st.POINT()
    if not windll.user32.GetCursorPos(byref(pt)):
        return 0
    return 1 if windll.user32.SetCursorPos(pt.x + int(dx), pt.y + int(dy)) else 0


def mouse_move(dx, dy, method="both"):
    if dx == 0 and dy == 0:
        return
    method = (method or "both").lower()
    if method in ("sendinput", "both"):
        _mouse_move_sendinput(dx, dy)
    if method in ("cursor", "both"):
        _mouse_move_cursor(dx, dy)


def mouse_wheel(direction):
    delta = st.WHEEL_DELTA if direction == "up" else -st.WHEEL_DELTA
    inp = st.INPUT(
        type=st.INPUT_MOUSE,
        u=st.INPUT_UNION(
            mi=st.MOUSEINPUT(0, 0, DWORD(delta & 0xFFFFFFFF), st.MOUSEEVENTF_WHEEL, 0, 0)
        ),
    )
    send_input(inp)


def mouse_center_screen():
    w = windll.user32.GetSystemMetrics(0)
    h = windll.user32.GetSystemMetrics(1)
    windll.user32.SetCursorPos(w // 2, h // 2)
