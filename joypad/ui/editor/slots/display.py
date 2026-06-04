"""Slot label rendering helpers."""

from joypad.input.bindings import binding_label
from joypad.ui.editor.slots.constants import STICK_MODE_LABELS


def _stick_label(mode):
    return STICK_MODE_LABELS.get(mode, mode or "—")


def _truncate_text(font, text, max_w):
    text = text or ""
    if max_w < 8 or font.size(text)[0] <= max_w:
        return text
    ell = "..."
    for n in range(len(text), 0, -1):
        trial = text[:n] + ell
        if font.size(trial)[0] <= max_w:
            return trial
    return ell


def _fit_row_label_value(font_label, font_val, label, value, width, gap=12):
    value = value or ""
    val_s = font_val.render(value, True, (255, 255, 255))
    val_w = val_s.get_width()
    label_max = max(20, width - val_w - gap)
    label_txt = _truncate_text(font_label, label, label_max)
    label_s = font_label.render(label_txt, True, (255, 255, 255))
    while label_s.get_width() + val_w + gap > width and len(label_txt) > 1:
        label_txt = _truncate_text(font_label, label_txt, label_max - 8)
        label_s = font_label.render(label_txt, True, (255, 255, 255))
        label_max -= 8
    return label_s, val_s, label_max


def _slot_display(slot):
    kind = slot["kind"]
    val = slot["value"]
    if kind in ("left_stick", "right_stick"):
        return _stick_label(val)
    if kind == "mouse_sens":
        return "%.1f" % float(val)
    if kind == "mouse_scale":
        return "%.1f" % float(val)
    if kind == "deadzone":
        return "%.2f" % float(val)
    if kind == "mouse_accel":
        return "%.2f" % float(val)
    if kind == "mouse_accel_off_lt":
        return "On" if val else "Off"
    return binding_label(val)
