from joypad.config import theme as launcher


def test_parse_color_hex_six():
    assert launcher._parse_color("#1a2b3c", (0, 0, 0)) == (0x1a, 0x2b, 0x3c)


def test_parse_color_hex_short():
    assert launcher._parse_color("#fff", (0, 0, 0)) == (255, 255, 255)


def test_parse_color_list():
    assert launcher._parse_color([10, 20, 30], (0, 0, 0)) == (10, 20, 30)


def test_parse_color_invalid_returns_default():
    assert launcher._parse_color("zzz", (1, 2, 3)) == (1, 2, 3)
    assert launcher._parse_color(None, (4, 5, 6)) == (4, 5, 6)


def test_parse_font_size_clamps():
    assert launcher._parse_font_size(5, 28, 12, 72) == 12
    assert launcher._parse_font_size(999, 28, 12, 72) == 72
    assert launcher._parse_font_size("30", 28, 12, 72) == 30
    assert launcher._parse_font_size(None, 28) == 28


def test_parse_font_bold():
    assert launcher._parse_font_bold("bold") is True
    assert launcher._parse_font_bold("normal") is False
    assert launcher._parse_font_bold(None, True) is True


def test_theme_from_config_defaults_and_overrides():
    theme = launcher._theme_from_config(
        {"theme": {"background": "#14141c", "font_size_title": 50}}
    )
    assert theme["background"] == (0x14, 0x14, 0x1c)
    assert theme["font_size_title"] == 50
    assert theme["text"] == launcher.TEXT_COLOR
    assert theme["font_size_list"] == 28
