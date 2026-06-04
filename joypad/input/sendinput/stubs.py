"""No-op SendInput stubs for non-Windows platforms."""

_send_input_errors = 0


def key_event(vk, down, method="scancode"):
    pass


def mouse_button(btn, down):
    pass


def mouse_move(dx, dy, method="both"):
    pass


def mouse_wheel(direction):
    pass


def mouse_center_screen():
    pass
