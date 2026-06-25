from joypad.ui.views.home.geometry import compute_home_geometry


def test_geometry_structure_and_bounds():
    g = compute_home_geometry(1280, 720, hint_line_h=26, title_line_h=52)
    assert g["rail_w"] == max(64, 1280 // 18)
    assert g["content_x"] == g["rail_w"]
    # hero sits right of the rail, inside margins
    assert g["hero"]["x"] >= g["rail_w"]
    assert g["hero"]["x"] + g["hero"]["w"] <= 1280
    # hero is roughly the top third-ish of the content height
    assert 0.30 <= g["hero"]["h"] / 720 <= 0.45
    # shelf area is below the hero and within the screen
    assert g["shelf_area"]["y"] >= g["hero"]["y"] + g["hero"]["h"]
    assert g["shelf_area"]["y"] + g["shelf_area"]["h"] <= 720
    # portrait tiles, 2:3
    assert g["tile_w"] == g["tile_h"] * 2 // 3
    assert g["shelf_stride"] == g["tile_h"] + g["shelf_label_h"] + g["tile_gap"]


def test_rail_minimum_on_small_screen():
    g = compute_home_geometry(640, 480, hint_line_h=20, title_line_h=42)
    assert g["rail_w"] == 64
    assert g["tile_h"] >= 48
