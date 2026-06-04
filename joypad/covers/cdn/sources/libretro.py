"""Libretro thumbnail URLs."""

import urllib.parse

from joypad.covers.cdn.sources.constants import _LIBRETRO_ART_KIND, _LIBRETRO_PLATFORMS


def libretro_urls(name):
    enc_name = urllib.parse.quote(name)
    urls = []
    for platform in _LIBRETRO_PLATFORMS:
        enc_plat = urllib.parse.quote(platform)
        for kind in _LIBRETRO_ART_KIND:
            urls.append(
                "https://thumbnails.libretro.com/%s/%s/%s.png"
                % (enc_plat, kind, enc_name)
            )
    return urls
