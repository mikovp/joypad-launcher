from joypad.app_state import AppState
from joypad.ui.views import tiles as tiles_mod


def test_compute_tile_grid_small_screen_scale_1():
    g = tiles_mod.compute_tile_grid(640, 480, hint_line_h=21, tile_scale=1.0)
    usable_w = 640 - 2 * g["side_margin"]
    assert g["cols"] >= 2
    assert g["tile_w"] == g["tile_h"]
    # at a modest scale the row of tiles fits inside the usable width
    assert g["cols"] * g["tile_w"] + g["gap"] * (g["cols"] - 1) <= usable_w
    expected_keys = {
        "cols", "tile_w", "tile_h", "gap", "selection_h", "grid_top",
        "grid_h", "side_margin", "grid_offset_x", "label_h", "top_banner",
        "bottom_hint", "section_header_h", "tile_scale",
    }
    assert expected_keys <= set(g.keys())


def test_compute_tile_grid_small_screen_large_scale_fits():
    # Regression: at 640x480 with tile_scale=2.5 the column count is capped so a
    # row of min-width tiles fits the usable width (previously the min_tile floor
    # made the row overflow). Fewer, bigger tiles instead of an overflowing row.
    g = tiles_mod.compute_tile_grid(640, 480, hint_line_h=21, tile_scale=2.5)
    usable_w = 640 - 2 * g["side_margin"]
    assert g["cols"] >= 2
    assert g["tile_w"] == g["tile_h"]
    assert g["cols"] * g["tile_w"] + g["gap"] * (g["cols"] - 1) <= usable_w


def test_compute_tile_grid_never_overflows_tiny_screens():
    # The row must never exceed the usable width across small screens and the
    # full range of tile scales (handhelds run at low resolutions).
    for w, h in [(480, 320), (640, 480), (800, 480), (960, 544), (1280, 720)]:
        for scale in (1.0, 2.5, 4.0, 6.0, 9.0):
            g = tiles_mod.compute_tile_grid(w, h, hint_line_h=21, tile_scale=scale)
            usable_w = w - 2 * g["side_margin"]
            row = g["cols"] * g["tile_w"] + g["gap"] * (g["cols"] - 1)
            assert g["cols"] >= 2
            assert row <= usable_w, (w, h, scale, row, usable_w)


def test_compute_tile_grid_ultrawide():
    g = tiles_mod.compute_tile_grid(3440, 1440, hint_line_h=21, tile_scale=2.5)
    usable_w = 3440 - 2 * g["side_margin"]
    assert g["cols"] >= 2
    assert g["tile_w"] == g["tile_h"]
    assert g["cols"] * g["tile_w"] + g["gap"] * (g["cols"] - 1) <= usable_w


class _FakeFont:
    def __init__(self, linesize):
        self._linesize = linesize

    def get_linesize(self):
        return self._linesize

    def size(self, text):
        return (len(text) * 10, self._linesize)


def _make_state(num_games):
    state = AppState()
    state.config = {"theme": {"tile_scale": 2.5}}
    state.w = 1920
    state.h = 1080
    state.hint_line_h = 21
    state.font_title = _FakeFont(40)
    state.font_hint = _FakeFont(21)
    state.tile_geom = tiles_mod.compute_tile_grid(
        1920, 1080, 21, tile_scale=2.5, title_line_h=40
    )
    state.tile_sections = [
        {"title": "Library", "games": [{"name": "g%d" % i} for i in range(num_games)]}
    ]
    return state


def test_rebuild_tile_layout_and_max_scroll():
    state = _make_state(20)
    tiles_mod.rebuild_tile_layout(state)
    assert len(state.tile_all_games) == 20
    kinds = {e["kind"] for e in state.tile_layout}
    assert kinds == {"header", "tile"}
    assert state.tile_layout[0] == {"kind": "header", "y": 0, "title": "Library"}
    # content taller than the grid viewport => positive max scroll
    assert state.tile_content_h > 0
    max_scroll = tiles_mod.tile_max_scroll_y(state)
    assert max_scroll == max(0, state.tile_content_h - state.tile_geom["grid_h"])
    assert max_scroll >= 0


def test_rebuild_tile_layout_empty_section_marks_empty():
    state = _make_state(0)
    tiles_mod.rebuild_tile_layout(state)
    assert state.tile_all_games == []
    kinds = {e["kind"] for e in state.tile_layout}
    assert "empty" in kinds
    # nothing scrollable: max scroll is non-negative
    assert tiles_mod.tile_max_scroll_y(state) >= 0
