"""List view selection and scroll."""


def move_selection_by_viewport(state, delta_pages):
    """Move highlight by roughly one screen (sum of game row heights), skipping category headers."""
    if delta_pages == 0:
        return
    step_px = max(int(state.viewport_h * 0.85), state.list_line_skip * 4)
    direction = 1 if delta_pages > 0 else -1
    pixels_moved = 0
    max_steps = len(state.list_items) + 2
    for _ in range(max_steps):
        if direction > 0:
            nxt = None
            for j in range(state.selected + 1, len(state.list_items)):
                if state.list_items[j]["kind"] == "game":
                    nxt = j
                    break
            if nxt is None:
                break
            pixels_moved += state.row_specs[nxt]["height"]
            state.selected = nxt
        else:
            nxt = None
            for j in range(state.selected - 1, -1, -1):
                if state.list_items[j]["kind"] == "game":
                    nxt = j
                    break
            if nxt is None:
                break
            pixels_moved += state.row_specs[nxt]["height"]
            state.selected = nxt
        if pixels_moved >= step_px:
            break


def page_scroll(state, delta_pages):
    move_selection_by_viewport(state, delta_pages)
    state.list_snap_scroll_to_selection = True


def _first_game_row_index(state):
    for i, it in enumerate(state.list_items):
        if it["kind"] == "game":
            return i
    return 0


def move_game_selection(state, delta):
    """Move selection only across game rows (skip category headers)."""
    n = len(state.list_items)
    if n == 0:
        return
    for _ in range(n):
        state.selected = (state.selected + delta) % n
        if state.list_items[state.selected]["kind"] == "game":
            state.list_snap_scroll_to_selection = True
            return


def snap_list_scroll(state):
    """Keep selected row on screen when list_snap_scroll_to_selection is set."""
    if state.ui_mode == "list" and state.list_snap_scroll_to_selection:
        sel_top = state.cum_starts[state.selected]
        sel_h = state.row_specs[state.selected]["height"]
        sel_bot = sel_top + sel_h
        if sel_top < state.list_scroll_y:
            state.list_scroll_y = sel_top
        elif sel_bot > state.list_scroll_y + state.viewport_h:
            state.list_scroll_y = sel_bot - state.viewport_h
    state.list_scroll_y = max(0, min(state.list_scroll_y, state.max_scroll_y))
