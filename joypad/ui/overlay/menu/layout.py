"""Settings menu layout and item lists."""

from joypad.config.settings import build_settings_menu


def settings_first_row(state):
    for i, it in enumerate(state.settings_menu_items):
        if it.get("kind") in ("setting", "action"):
            return i
    return 0


def rebuild_settings_layout(state):
    state.settings_menu_items = build_settings_menu(state.config)
    cat_skip = state.font_category.get_linesize() + 8
    setting_h = state.font_list.get_linesize() + 8
    state.settings_cum_starts = []
    state.settings_row_specs = []
    y_acc = 0
    for item in state.settings_menu_items:
        state.settings_cum_starts.append(y_acc)
        if item.get("kind") == "header":
            h_row = cat_skip
            state.settings_row_specs.append({"kind": "header", "height": h_row, "title": item["title"]})
        else:
            h_row = setting_h
            state.settings_row_specs.append({"kind": "row", "height": h_row, "item": item})
        y_acc += h_row
    state.settings_content_h = y_acc


def overlay_items(state):
    return state.settings_menu_items if state.overlay_menu == "settings" else state.system_menu_items
