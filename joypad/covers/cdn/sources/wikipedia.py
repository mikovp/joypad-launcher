"""Wikipedia REST summary thumbnails."""

import urllib.parse

from joypad.covers.cdn.http import http_json


def wikipedia_thumbnail_url(name, timeout=12):
    """Wikipedia REST summary — free thumbnail when article exists."""
    if not name:
        return None
    titles = [name.strip()]
    if " / " in name:
        titles.append(name.split(" / ")[-1].strip())
    for title in titles:
        enc = urllib.parse.quote(title.replace(" ", "_"))
        data = http_json(
            "https://en.wikipedia.org/api/rest_v1/page/summary/%s" % enc,
            timeout,
        )
        if not data:
            continue
        thumb = data.get("thumbnail") or {}
        src = thumb.get("source")
        if isinstance(src, str) and src.startswith("http"):
            return src
    return None
