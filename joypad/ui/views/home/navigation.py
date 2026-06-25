"""Home view focus model and movement. Pure (no pygame)."""

RAIL_ITEMS = ["home", "settings", "power"]


def home_init_focus(state):
    if state.home_shelves:
        state.home_focus = {"zone": "shelf", "shelf": 0, "col": 0, "rail": 0}
    else:
        state.home_focus = {"zone": "rail", "shelf": 0, "col": 0, "rail": 0}


def _focused_shelf(state):
    shelves = state.home_shelves or []
    f = state.home_focus
    if not shelves or not f:
        return None
    return shelves[min(f["shelf"], len(shelves) - 1)]


def home_selected_game(state):
    f = state.home_focus
    if not f or f["zone"] not in ("shelf", "hero"):
        return None
    shelf = _focused_shelf(state)
    if not shelf or not shelf["games"]:
        return None
    col = min(f["col"], len(shelf["games"]) - 1)
    return shelf["games"][col]
