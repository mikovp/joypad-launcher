"""Remote cover URL sources (Steam, Libretro, Wikipedia, RAWG)."""

from joypad.covers.cdn.sources.aggregate import cdn_urls_for_game
from joypad.covers.cdn.sources.names import art_name_variants
from joypad.covers.cdn.sources.rawg import rawg_fetch_url
from joypad.covers.cdn.sources.steam import steam_cdn_urls, steam_store_search_app_id

__all__ = [
    "art_name_variants",
    "cdn_urls_for_game",
    "rawg_fetch_url",
    "steam_cdn_urls",
    "steam_store_search_app_id",
]
