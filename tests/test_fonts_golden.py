from joypad.ui import fonts as launcher
from joypad.ui import fonts as jp_fonts


class FakeFont:
    """Monospace-ish: width = chars * 10 px."""
    def size(self, text):
        return (len(text) * 10, 12)


def test_wrap_words_to_width_breaks_on_space():
    font = FakeFont()
    lines = launcher._wrap_words_to_width(font, "aa bb cc", 50)  # 5 chars/line
    assert lines == ["aa bb", "cc"]


def test_hard_break_long_word():
    font = FakeFont()
    lines = launcher._hard_break_word(font, "abcdef", 30)  # 3 chars/line
    assert lines == ["abc", "def"]


def test_fonts_module_direct_matches():
    font = FakeFont()
    assert jp_fonts._wrap_words_to_width(font, "aa bb cc", 50) == ["aa bb", "cc"]
    assert jp_fonts._hard_break_word(font, "abcdef", 30) == ["abc", "def"]
