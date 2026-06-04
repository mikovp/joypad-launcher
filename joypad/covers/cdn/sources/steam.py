"""Steam CDN and store search URLs."""

import urllib.parse

from joypad.covers.cdn.http import http_json
from joypad.covers.cdn.sources.constants import _STEAM_CDN_TEMPLATES, _STEAM_STORE_SEARCH


def steam_cdn_urls(app_id):
    aid = str(app_id)
    return [tpl.format(id=aid) for tpl in _STEAM_CDN_TEMPLATES]


def steam_store_search_app_id(name, timeout=12, cache=None):
    """
    Free Steam store search API (no key). Returns app id string or None.
    """
    if not name:
        return None
    key = name.strip().lower()
    if cache is not None and key in cache:
        return cache[key]

    url = _STEAM_STORE_SEARCH.format(term=urllib.parse.quote(name.strip()))
    data = http_json(url, timeout)
    if not data:
        if cache is not None:
            cache[key] = None
        return None

    items = data.get("items") or []
    app_id = None
    name_l = key
    for item in items:
        if not isinstance(item, dict):
            continue
        iname = (item.get("name") or "").strip().lower()
        iid = item.get("id")
        if iid is None:
            continue
        if iname == name_l:
            app_id = str(iid)
            break
    if app_id is None and items:
        first = items[0]
        if isinstance(first, dict) and first.get("id") is not None:
            app_id = str(first["id"])

    if cache is not None:
        cache[key] = app_id
    return app_id
