"""Editor grid scroll and slot positioning."""

from joypad.ui.editor.layout import editor_areas, grid_header_h
from joypad.ui.editor.slots import FACE_COL_INDEX, _grid_column_specs


def grid_max_scroll(session, areas):
    header_h = grid_header_h(session)
    visible = max(1, areas["grid_rows_h"] - header_h)
    face_line_h = areas["face_line_h"]
    _, indices = _grid_column_specs(session.slots)[FACE_COL_INDEX]
    n = sum(1 for idx in indices if idx is not None)
    return max(0, n * face_line_h - visible)


def slot_grid_pos(session, slot_index, areas):
    line_h = areas["line_h"]
    face_line_h = areas["face_line_h"]
    for col, (_, indices) in enumerate(_grid_column_specs(session.slots)):
        col_h = face_line_h if col == FACE_COL_INDEX else line_h
        row = 0
        for idx in indices:
            if idx is None:
                continue
            if idx == slot_index:
                return col, row, col_h
            row += col_h
    return None


def snap_grid_scroll(session, areas=None):
    if session.mode != "editor":
        return
    if areas is None:
        w, h = session.screen.get_size()
        areas = editor_areas(session, w, h)
    pos = slot_grid_pos(session, session.slot_index, areas)
    if pos is None:
        return
    col, rel_y, row_h = pos
    if col != FACE_COL_INDEX:
        return
    header_h = grid_header_h(session)
    visible = max(1, areas["grid_rows_h"] - header_h)
    max_scroll = grid_max_scroll(session, areas)
    if rel_y < session.scroll:
        session.scroll = rel_y
    elif rel_y + row_h > session.scroll + visible:
        session.scroll = rel_y + row_h - visible
    session.scroll = max(0, min(max_scroll, session.scroll))


def scroll_grid(session, delta_pages):
    if session.mode != "editor":
        return
    w, h = session.screen.get_size()
    areas = editor_areas(session, w, h)
    step = max(areas["face_line_h"] * 3, 36)
    max_scroll = grid_max_scroll(session, areas)
    session.scroll = max(0, min(max_scroll, session.scroll + delta_pages * step))
