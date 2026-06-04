"""Parse theme values from config JSON."""


def parse_color(value, default):
    """Converts config value to (R, G, B) tuple."""
    if value is None:
        return default
    if isinstance(value, str):
        s = value.strip().lstrip("#")
        try:
            if len(s) == 6:
                r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
                return (r, g, b)
            if len(s) == 3:
                r = int(s[0], 16) * 17
                g = int(s[1], 16) * 17
                b = int(s[2], 16) * 17
                return (r, g, b)
        except (ValueError, IndexError):
            pass
        return default
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            r, g, b = int(value[0]), int(value[1]), int(value[2])
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return (r, g, b)
        except (TypeError, ValueError):
            pass
    return default


def parse_font_size(value, default, min_size=12, max_size=120):
    if value is None:
        return default
    try:
        size = int(value)
        return max(min_size, min(max_size, size))
    except (TypeError, ValueError):
        return default


def parse_font_bold(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("bold", "true", "1", "yes"):
            return True
        if s in ("normal", "regular", "false", "0", "no"):
            return False
    return default


def parse_font_scale(value, default=1.0):
    if value is None:
        return default
    try:
        x = float(value)
        return x if x > 0 else default
    except (TypeError, ValueError):
        return default


def parse_positive_float(value, default):
    if value is None:
        return default
    try:
        x = float(value)
        return x if x > 0 else default
    except (TypeError, ValueError):
        return default
