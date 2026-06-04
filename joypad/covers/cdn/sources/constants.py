"""CDN URL templates and platform lists."""

_STEAM_CDN_TEMPLATES = (
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/library_600x900.jpg",
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/library_hero.jpg",
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/header.jpg",
    "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{id}/library_600x900.jpg",
    "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{id}/library_hero.jpg",
    "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{id}/header.jpg",
)

_STEAM_STORE_SEARCH = "https://store.steampowered.com/api/storesearch/?term={term}&l=english&cc=US"

_LIBRETRO_PLATFORMS = (
    "Nintendo - Nintendo Switch",
    "Sony - PlayStation 4",
    "Sony - PlayStation 3",
    "Sony - PlayStation 2",
    "Microsoft - Xbox 360",
    "Microsoft - Xbox",
    "Nintendo - Wii U",
    "Nintendo - Wii",
    "Nintendo - GameCube",
    "Nintendo - Nintendo 64",
    "Nintendo - Super Nintendo Entertainment System",
    "Sega - Dreamcast",
    "Nintendo - Nintendo DS",
    "Nintendo - Game Boy Advance",
)

_LIBRETRO_ART_KIND = ("Named_Boxarts", "Named_Titles")

_LIBRETRO_SWITCH_ONLY = (
    "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20Switch/Named_Boxarts/{name}.png",
    "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20Switch/Named_Titles/{name}.png",
)
