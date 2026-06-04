"""Aggregate remote cover URLs for a game."""

import urllib.parse

from joypad.covers.cdn.nsp import nsp_art_name, nsp_title_id_cdn_urls
from joypad.covers.cdn.sources.constants import _LIBRETRO_SWITCH_ONLY
from joypad.covers.cdn.sources.libretro import libretro_urls
from joypad.covers.cdn.sources.names import art_name_variants
from joypad.covers.cdn.sources.steam import steam_cdn_urls, steam_store_search_app_id
from joypad.covers.cdn.sources.wikipedia import wikipedia_thumbnail_url
from joypad.integrations.twitch import normalize_platform


def cdn_urls_for_game(game, steam_search_cache=None):
    """Ordered remote image URLs (all free, no API key)."""
    platform = normalize_platform(game.get("platform"))
    urls = []
    seen = set()

    def add(u):
        if u and u not in seen:
            seen.add(u)
            urls.append(u)

    if platform == "steam" and game.get("steam_app_id"):
        for u in steam_cdn_urls(game["steam_app_id"]):
            add(u)

    epic_url = game.get("epic_image_url")
    if isinstance(epic_url, str) and epic_url.startswith("http"):
        add(epic_url.strip())

    if platform == "twitch":
        raw_stem = (game.get("nsp_filename") or nsp_art_name(game) or "").strip()
        for u in nsp_title_id_cdn_urls(raw_stem):
            add(u)
        for name in art_name_variants(game):
            enc = urllib.parse.quote(name)
            for tpl in _LIBRETRO_SWITCH_ONLY:
                add(tpl.format(name=enc))
        for name in art_name_variants(game):
            for u in libretro_urls(name):
                add(u)
    else:
        for name in art_name_variants(game):
            for u in libretro_urls(name):
                add(u)

    if platform != "steam" or not game.get("steam_app_id"):
        for name in art_name_variants(game):
            app_id = steam_store_search_app_id(name, cache=steam_search_cache)
            if app_id:
                for u in steam_cdn_urls(app_id):
                    add(u)

    for name in art_name_variants(game):
        wiki = wikipedia_thumbnail_url(name)
        if wiki:
            add(wiki)

    return urls
