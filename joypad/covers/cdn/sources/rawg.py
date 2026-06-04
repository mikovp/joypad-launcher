"""Optional RAWG API cover lookup."""

import urllib.parse

from joypad.covers.cdn.http import http_json


def rawg_fetch_url(game, api_key, timeout=12):
    """Optional: only if user set rawg_api_key in config."""
    name = (game.get("name") or "").strip()
    if not name or not api_key:
        return None
    q = urllib.parse.quote(name)
    url = "https://api.rawg.io/api/games?search=%s&page_size=1&key=%s" % (q, urllib.parse.quote(api_key))
    data = http_json(url, timeout)
    if not data:
        return None
    results = data.get("results") or []
    if not results:
        return None
    img = results[0].get("background_image") or results[0].get("background_image_additional")
    if isinstance(img, str) and img.startswith("http"):
        return img
    return None
