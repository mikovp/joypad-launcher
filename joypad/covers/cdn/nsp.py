"""Twitch/NSP cover filename parsing and search stems."""

import os
import re

# NSP filenames on disk (examples from user library):
#   Super Mario Bros. Wonder [010015100B514000][v0].nsp
#   No Mans Sky [0100853015E86800][v4915200].nsp
#   STALKER ... [01004A001E32E000][v0] (7.41 GB).nsp
_NSP_DUMP_SUFFIX_RE = re.compile(
    r"\s*"
    r"(?:\[[0-9A-Fa-f]{16}\]\s*\[v\d+\])"  # Switch title ID + version
    r"(?:\s*\([\d.]+\s*(?:GB|MB|GiB|MiB)\))?"  # optional "(7.41 GB)"
    r"\s*$",
    re.IGNORECASE,
)
_NSP_SIZE_SUFFIX_RE = re.compile(
    r"\s*\([\d.]+\s*(?:GB|MB|GiB|MiB)\)\s*$",
    re.IGNORECASE,
)
_NSP_TITLE_ID_RE = re.compile(r"\[([0-9A-Fa-f]{16})\]")


def nsp_art_name(game):
    """NSP cover lookup uses the .nsp filename (stem), not the folder display name."""
    path = game.get("nsp_path") or ""
    return os.path.splitext(os.path.basename(path))[0]


def nsp_title_id_cdn_urls(stem):
    """Switch cover by 16-digit title ID embedded in the .nsp filename."""
    m = _NSP_TITLE_ID_RE.search(stem or "")
    if not m:
        return []
    tid = m.group(1).upper()
    return ["https://tinfoil.media/ti/%s/0/0" % tid]


def nsp_title_aliases(title):
    """
    Extra search names when the filename omits punctuation (e.g. STALKER vs S.T.A.L.K.E.R.).
    """
    aliases = []
    t = (title or "").strip()
    if not t:
        return aliases

    if re.match(r"^STALKER\b", t, re.I) and "S.T.A.L.K.E.R" not in t.upper():
        dotted = re.sub(r"^STALKER\b", "S.T.A.L.K.E.R.", t, count=1, flags=re.I)
        aliases.append(dotted)
        if ":" not in dotted:
            aliases.append(re.sub(r"^S\.T\.A\.L\.K\.E\.R\.\s+", "S.T.A.L.K.E.R.: ", dotted, count=1))

    if "chornobyl" in t.lower():
        aliases.append(re.sub(r"chornobyl", "Chernobyl", t, flags=re.I))
    if "chernobyl" in t.lower() and "chornobyl" not in t.lower():
        aliases.append(re.sub(r"chernobyl", "Chornobyl", t, flags=re.I))

    return aliases


def nsp_cover_stems(game):
    """
    Variants from the .nsp filename only (not the folder display name in the list).
    """
    stem = (game.get("nsp_filename") or nsp_art_name(game) or "").strip()
    if not stem:
        return []

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

    add(stem)
    no_dump = _NSP_DUMP_SUFFIX_RE.sub("", stem).strip()
    if no_dump:
        add(no_dump)
    no_size = _NSP_SIZE_SUFFIX_RE.sub("", no_dump or stem).strip()
    if no_size:
        add(no_size)
    head = stem.split("[", 1)[0].strip() if "[" in stem else ""
    if head:
        add(head)

    for base in (no_dump, no_size, head):
        if not base:
            continue
        for alt in nsp_title_aliases(base):
            add(alt)

    return out
