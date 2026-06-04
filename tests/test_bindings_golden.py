from joypad.input import bindings as input_remap


def test_cycle_binding_advances_and_wraps():
    bindings = input_remap.BUTTON_BINDINGS
    first = bindings[0][0]
    second = bindings[1][0]
    last = bindings[-1][0]
    assert input_remap.cycle_binding(first) == second
    assert input_remap.cycle_binding(last) == first


def test_binding_label_known_and_unknown():
    assert input_remap.binding_label("none") == "—"
    assert input_remap.binding_label("definitely_not_a_binding") == "definitely_not_a_binding"


def test_cycle_stick_mode():
    assert input_remap.cycle_stick_mode("none") == "wasd"
    assert input_remap.cycle_stick_mode("arrows") == "none"
    assert input_remap.cycle_right_stick_mode("none") == "mouse"
    assert input_remap.cycle_right_stick_mode("mouse") == "none"
