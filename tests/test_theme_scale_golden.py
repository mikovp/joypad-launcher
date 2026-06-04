import copy

from joypad.config import theme as t


def test_scale_fonts_boost_low_res_when_enabled():
    base = t.theme_from_config({"theme": {}})
    assert base["font_size_title"] == 42
    assert base["font_size_list"] == 28

    th = copy.deepcopy(base)
    t.scale_theme_fonts_for_screen(th, {"auto_font_boost_low_res": True}, 720)
    # 1080/720 = 1.5 factor: 42*1.5=63, 28*1.5=42
    assert th["font_size_title"] == 63
    assert th["font_size_list"] == 42


def test_scale_fonts_clamped_to_boost_max():
    base = t.theme_from_config({"theme": {}})
    th = copy.deepcopy(base)
    # tiny height would imply huge factor, but boost_max defaults to 1.65
    t.scale_theme_fonts_for_screen(th, {"auto_font_boost_low_res": True}, 200)
    # 42*1.65=69.3 -> 69, 28*1.65=46.2 -> 46
    assert th["font_size_title"] == 69
    assert th["font_size_list"] == 46
    # within documented output clamps (12..96 title, 12..72 list)
    assert 12 <= th["font_size_title"] <= 96
    assert 12 <= th["font_size_list"] <= 72


def test_scale_fonts_no_boost_when_disabled():
    base = t.theme_from_config({"theme": {}})
    th = copy.deepcopy(base)
    t.scale_theme_fonts_for_screen(th, {"auto_font_boost_low_res": False}, 720)
    assert th["font_size_title"] == 42
    assert th["font_size_list"] == 28


def test_parse_tile_scale_passthrough_and_clamp():
    assert t.parse_tile_scale(3.0, 2.5) == 3.0
    # upper clamp 9.0, lower clamp 0.5
    assert t.parse_tile_scale(100, 2.5) == 9.0
    assert t.parse_tile_scale(0.1, 2.5) == 0.5


def test_parse_tile_scale_junk_and_none_return_default():
    assert t.parse_tile_scale("abc", 2.5) == 2.5
    assert t.parse_tile_scale(None, 2.5) == 2.5
