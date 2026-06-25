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


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _shelf_len(state, shelf_i):
    shelves = state.home_shelves or []
    if not shelves:
        return 0
    return len(shelves[_clamp(shelf_i, 0, len(shelves) - 1)]["games"])


def home_move(state, dx, dy):
    shelves = state.home_shelves or []
    f = state.home_focus
    if not f:
        home_init_focus(state)
        f = state.home_focus
    zone = f["zone"]

    if zone == "rail":
        if dy:
            f["rail"] = _clamp(f["rail"] + dy, 0, len(RAIL_ITEMS) - 1)
        if dx > 0:
            f["zone"] = "shelf" if shelves else "rail"
        return

    if zone == "hero":
        if dy > 0:
            f["zone"] = "shelf"
            f["shelf"] = 0
            f["col"] = _clamp(f["col"], 0, max(0, _shelf_len(state, 0) - 1))
        return

    # zone == "shelf"
    if dx < 0 and f["col"] == 0:
        f["zone"] = "rail"
        return
    if dx:
        f["col"] = _clamp(f["col"] + dx, 0, max(0, _shelf_len(state, f["shelf"]) - 1))
    if dy < 0 and f["shelf"] == 0:
        f["zone"] = "hero"
        return
    if dy:
        f["shelf"] = _clamp(f["shelf"] + dy, 0, max(0, len(shelves) - 1))
        f["col"] = _clamp(f["col"], 0, max(0, _shelf_len(state, f["shelf"]) - 1))


def home_lb_rb(state, delta):
    f = state.home_focus
    if f and f["zone"] == "shelf":
        home_move(state, 0, delta)
