"""Mapping grid columns and settings rows."""

import pygame

from joypad.input.constants import BTN_A, BTN_B, BTN_X, BTN_Y
from joypad.ui.editor.drawing.grid.row import draw_grid_row
from joypad.ui.editor.layout import grid_header_h
from joypad.ui.editor.slots import (
    FACE_BTN_COLORS,
    FACE_COL_INDEX,
    OUTLINE_COLOR,
    _grid_column_specs,
    _slot_index,
)


def draw_mapping_grid(session, areas):
    x0 = areas["content_x"]
    w = areas["content_w"]
    y = areas["grid_top"]
    line_h = areas["line_h"]
    face_line_h = areas["face_line_h"]
    col_w = w // 4
    row_inner = col_w - 28
    header_h = grid_header_h(session)
    list_top = y + header_h
    list_bottom = y + areas["grid_rows_h"]

    session._snap_grid_scroll(areas)

    columns = _grid_column_specs(session.slots)
    face_labels = {str(BTN_A): "A", str(BTN_B): "B", str(BTN_X): "X", str(BTN_Y): "Y"}
    dpad_short = {
        "dpad_up": "Up",
        "dpad_down": "Down",
        "dpad_left": "Left",
        "dpad_right": "Right",
    }

    pygame.draw.line(session.screen, OUTLINE_COLOR, (x0, y), (x0 + w, y), 1)

    for col, (header, _) in enumerate(columns):
        cx = x0 + col * col_w + 12
        hdr = session.font_list.render(header, True, session.title)
        session.screen.blit(hdr, (cx, y + 6))

    def _draw_column(col, indices, scroll_offset=0, clip=None):
        cx = x0 + col * col_w + 12
        col_line_h = face_line_h if col == FACE_COL_INDEX else line_h
        prev_clip = None
        if clip is not None:
            prev_clip = session.screen.get_clip()
            session.screen.set_clip(clip)
        rel_y = 0
        for idx in indices:
            if idx is None:
                continue
            draw_y = list_top + rel_y - scroll_offset
            if draw_y + col_line_h > list_top and draw_y < list_bottom:
                slot = session.slots[idx]
                if slot["kind"] == "dpad":
                    label = dpad_short.get(slot["key"], slot["label"])
                elif slot["kind"] == "stick_click":
                    label = slot["label"]
                elif slot["kind"] == "chord":
                    label = slot["label"].replace("Button ", "")
                elif slot["kind"] == "button" and slot["key"] in face_labels:
                    label = face_labels[slot["key"]]
                else:
                    label = slot["label"]
                color = None
                if slot["kind"] == "button" and slot["key"] in face_labels:
                    color = FACE_BTN_COLORS.get(slot["key"])
                elif slot["kind"] == "chord" and slot.get("key", "").startswith(("lb_", "rb_")):
                    color = (120, 130, 150)
                draw_grid_row(session, cx, draw_y, row_inner, col_line_h, label, idx, color)
            rel_y += col_line_h
        if clip is not None:
            session.screen.set_clip(prev_clip)

    for col in range(FACE_COL_INDEX):
        _, indices = columns[col]
        _draw_column(col, indices)

    face_x = x0 + FACE_COL_INDEX * col_w
    face_clip = pygame.Rect(face_x, list_top, col_w, max(1, list_bottom - list_top))
    _, face_indices = columns[FACE_COL_INDEX]
    _draw_column(FACE_COL_INDEX, face_indices, scroll_offset=session.scroll, clip=face_clip)

    settings_y = areas["settings_y"]
    pygame.draw.line(session.screen, OUTLINE_COLOR, (x0, settings_y - 6), (x0 + w, settings_y - 6), 1)
    ms = _slot_index(session.slots, "mouse_sens")
    msc = _slot_index(session.slots, "mouse_scale")
    dz = _slot_index(session.slots, "deadzone")
    ma = _slot_index(session.slots, "mouse_accel")
    maolt = _slot_index(session.slots, "mouse_accel_off_lt")
    setting_w = w // 3 - 24
    setting_w2 = w // 2 - 24
    settings_row2_y = settings_y + line_h + 6
    if ms is not None:
        draw_grid_row(session, x0 + 12, settings_y, setting_w, line_h, "Mouse speed", ms)
    if msc is not None:
        draw_grid_row(session, x0 + w // 3 + 12, settings_y, setting_w, line_h, "Mouse scale", msc)
    if dz is not None:
        draw_grid_row(session, x0 + 2 * w // 3 + 12, settings_y, setting_w, line_h, "Deadzone", dz)
    if ma is not None:
        draw_grid_row(session, x0 + 12, settings_row2_y, setting_w2, line_h, "Mouse accel", ma)
    if maolt is not None:
        draw_grid_row(
            session, x0 + w // 2 + 12, settings_row2_y, setting_w2, line_h, "Accel off LT", maolt
        )
