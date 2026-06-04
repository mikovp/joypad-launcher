"""List view row layout computation."""

from joypad.ui.fonts import wrap_words_to_width


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
