"""Keyboard injection via SendInput."""

from ctypes import windll

from joypad.input.sendinput.win32 import structures as st
from joypad.input.sendinput.win32.core import send_input


def _key_event_vk(vk, down):
    flags = 0 if down else st.KEYEVENTF_KEYUP
    inp = st.INPUT(
        type=st.INPUT_KEYBOARD,
        u=st.INPUT_UNION(ki=st.KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)),
    )
    send_input(inp)


def _key_event_scancode(vk, down):
    scan = windll.user32.MapVirtualKeyW(vk, st.MAPVK_VK_TO_VSC) & 0xFF
    if not scan:
        _key_event_vk(vk, down)
        return
    flags = st.KEYEVENTF_SCANCODE
    if not down:
        flags |= st.KEYEVENTF_KEYUP
    if vk in st._EXTENDED_VKS:
        flags |= st.KEYEVENTF_EXTENDEDKEY
    inp = st.INPUT(
        type=st.INPUT_KEYBOARD,
        u=st.INPUT_UNION(
            ki=st.KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
        ),
    )
    send_input(inp)


def key_event(vk, down, method="scancode"):
    method = (method or "scancode").lower()
    if method == "vk":
        _key_event_vk(vk, down)
    elif method == "both":
        _key_event_scancode(vk, down)
        _key_event_vk(vk, down)
    else:
        _key_event_scancode(vk, down)
