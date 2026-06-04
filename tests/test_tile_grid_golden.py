from joypad.ui.views import tiles as launcher


def test_compute_tile_grid_invariants_1080p():
    grid = launcher.compute_tile_grid(1920, 1080, hint_line_h=21, tile_scale=2.5)
    assert grid["cols"] >= 2
    assert grid["tile_w"] == grid["tile_h"]
    usable_w = 1920 - 2 * grid["side_margin"]
    assert grid["cols"] * grid["tile_w"] + grid["gap"] * (grid["cols"] - 1) <= usable_w
    assert grid["tile_scale"] == 2.5


def test_compute_tile_grid_smaller_scale_more_cols():
    big = launcher.compute_tile_grid(1920, 1080, 21, tile_scale=4.0)
    small = launcher.compute_tile_grid(1920, 1080, 21, tile_scale=1.0)
    assert small["cols"] >= big["cols"]
