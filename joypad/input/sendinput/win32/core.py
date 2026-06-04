"""Low-level SendInput wrapper."""

from ctypes import sizeof, windll

from joypad.input.log import remap_log
from joypad.input.sendinput.win32 import structures as st


def send_input(*inputs):
    arr = (st.INPUT * len(inputs))(*inputs)
    sent = windll.user32.SendInput(len(inputs), arr, sizeof(st.INPUT))
    if sent != len(inputs):
        st._send_input_errors += 1
        if st._send_input_errors <= 5:
            remap_log("SendInput sent %s/%s (err=%s)" % (sent, len(inputs), windll.kernel32.GetLastError()))
    return sent
