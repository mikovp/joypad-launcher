"""Game name variants for cover search."""

import os

from joypad.covers.cdn.nsp import nsp_cover_stems
from joypad.integrations.twitch import normalize_platform


def art_name_variants(game):
    """Names to try on Libretro / Steam search / Wikipedia."""
    if normalize_platform(game.get("platform")) == "twitch":
        return nsp_cover_stems(game)

    seen = set()
    out = []

    def add(val):
        val = (val or "").strip()
        if not val:
            return
        key = val.lower()
        if key not in seen:
            seen.add(key)
            out.append(val)

    add(game.get("name"))
    name = (game.get("name") or "").strip()
    if " / " in name:
        add(name.split(" / ")[-1])
    exe = game.get("exe_path")
    if exe:
        add(os.path.splitext(os.path.basename(exe))[0])
    return out
