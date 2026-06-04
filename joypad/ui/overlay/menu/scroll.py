"""Overlay menu navigation and scroll snapping."""

from joypad.ui.overlay.menu.layout import overlay_items


def overlay_snap_scroll(state):
    if state.overlay_menu != "settings" or not state.settings_row_specs:
        return
    header_h = 48
    max_menu_h = max(120, state.h - 80)
    body_h = max_menu_h - header_h
    max_scroll = max(0, state.settings_content_h - body_h)
    sel_top = state.settings_cum_starts[state.overlay_index]
    sel_h = state.settings_row_specs[state.overlay_index]["height"]
    sel_bot = sel_top + sel_h
    if sel_top < state.overlay_scroll_y:
        state.overlay_scroll_y = sel_top
    elif sel_bot > state.overlay_scroll_y + body_h:
        state.overlay_scroll_y = sel_bot - body_h
    state.overlay_scroll_y = max(0, min(state.overlay_scroll_y, max_scroll))


def overlay_move(state, delta):
    if state.overlay_menu == "settings":
        n = len(state.settings_menu_items)
        if n == 0:
            return
        for _ in range(n):
            state.overlay_index = (state.overlay_index + delta) % n
            if state.settings_menu_items[state.overlay_index].get("kind") in ("setting", "action"):
                break
        overlay_snap_scroll(state)
        return
    items = overlay_items(state)
    state.overlay_index = (state.overlay_index + delta) % len(items)
    menu_line_h = state.font_list.get_linesize() + 8
    header_h = 48
    max_menu_h = max(120, state.h - 80)
    body_h = max_menu_h - header_h
    max_scroll = max(0, len(items) * menu_line_h - body_h)
    row_top = state.overlay_index * menu_line_h
    row_bot = row_top + menu_line_h
    if row_top < state.overlay_scroll_y:
        state.overlay_scroll_y = row_top
    elif row_bot > state.overlay_scroll_y + body_h:
        state.overlay_scroll_y = min(max_scroll, row_bot - body_h)
    state.overlay_scroll_y = max(0, min(state.overlay_scroll_y, max_scroll))
