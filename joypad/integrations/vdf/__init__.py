"""Valve Data Format (VDF) parsing for Steam library files."""

try:
    import vdf
except ImportError:
    vdf = None

from joypad.integrations.vdf.simple import parse_vdf_simple


def parse_vdf(path):
    """Reads VDF file and returns dict. Uses vdf first, fallback to built-in parser."""
    if vdf:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return vdf.load(f)
        except Exception:
            pass
    return parse_vdf_simple(path)


__all__ = ["parse_vdf", "parse_vdf_simple"]
