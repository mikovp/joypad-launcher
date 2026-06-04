"""List-view rendering and navigation for the launcher.

Module-level extraction of the list/navigation-cluster functions formerly
nested in run_launcher. Each function takes ``state`` (an AppState) as its first
argument; read-only session data (w, list_items, game_row_numbers, margin_right,
list_left) is carried on ``state`` as well. Navigation functions dispatch on
``state.ui_mode`` and delegate to the tile cluster in ``joypad.ui.views.tiles``.
"""

from joypad.ui.fonts import wrap_words_to_width
from joypad.ui.views import tiles


def build_list_layout(state):
    cat_skip = state.font_category.get_linesize() + 8
    max_right = state.w - state.margin_right
    state.cum_starts = []
    specs = []
    y_acc = 0
    for idx, item in enumerate(state.list_items):
        state.cum_starts.append(y_acc)
        if item["kind"] == "header":
            h_row = cat_skip
            specs.append({"kind": "header", "height": h_row, "title": item["title"]})
        else:
            num = state.game_row_numbers[idx]
            prefix = "    %d. " % num
            pw = state.font_list.size(prefix)[0]
            x_text = state.list_left + pw
            usable = max(48, max_right - x_text)
            name = item["game"].get("name", "Untitled")
            name_lines = wrap_words_to_width(state.font_list, name, usable)
            h_row = max(state.list_line_skip, len(name_lines) * state.list_line_skip + 6)
            specs.append({
                "kind": "game",
                "height": h_row,
                "prefix": prefix,
                "name_lines": name_lines,
                "x_text": x_text,
            })
        y_acc += h_row
    total_h = y_acc
    return state.cum_starts, specs, total_h


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


def _hint_surfaces(state):
    if state.ui_mode == "tiles":
        title = state.font_hint.render("Pick a game (tiles)", True, state.title_color)
        hint = state.font_hint.render(
            "A — launch   B — menu   ←→↑↓   LB/RB — library (1st tile)   LT/RT — scroll",
            True,
            state.title_color,
        )
    else:
        title = state.font_hint.render("Select a game or action (gamepad or keyboard)", True, state.title_color)
        hint = state.font_hint.render(
            "A / Enter — launch   B / Esc — menu   ↑↓ row   PgUp/PgDn   LB/RB   LT/RT — page",
            True,
            state.title_color,
        )
    return title, hint


def get_selected_item(state):
    if state.ui_mode == "tiles":
        g = tiles.tile_selected_game(state)
        if g is None:
            return None
        return {"kind": "game", "game": g}
    if 0 <= state.selected < len(state.list_items) and state.list_items[state.selected]["kind"] == "game":
        return state.list_items[state.selected]
    return None


def nav_vertical(state, delta):
    if state.ui_mode == "tiles":
        tiles.tile_move(state, 0, delta)
    else:
        move_game_selection(state, delta)


def nav_horizontal(state, delta):
    if state.ui_mode == "tiles":
        tiles.tile_move(state, delta, 0)


def nav_page(state, delta):
    if state.ui_mode == "tiles":
        tiles.tile_page_scroll(state, delta)
    else:
        page_scroll(state, delta)


def nav_lb_rb(state, delta):
    if state.ui_mode == "tiles":
        _sec_i, local = tiles._tile_pick_location(state, state.tile_pick)
        if local == 0:
            tiles.tile_section_jump(state, delta)
        else:
            tiles.tile_page_scroll(state, delta)
    else:
        page_scroll(state, delta)
