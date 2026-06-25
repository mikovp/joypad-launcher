"""Home view geometry: rail, hero, horizontal shelves. Pure (no pygame)."""


def compute_home_geometry(w, h, hint_line_h, title_line_h):
    rail_w = max(64, w // 18)
    margin = max(16, w // 60)
    content_x = rail_w
    content_w = w - rail_w

    top = max(24, title_line_h + 16)            # leave room for the screen title
    hero_h = int((h - top) * 0.38)
    hero = {
        "x": content_x + margin,
        "y": top,
        "w": content_w - 2 * margin,
        "h": hero_h,
    }

    shelf_y = hero["y"] + hero["h"] + margin
    shelf_area = {
        "x": content_x + margin,
        "y": shelf_y,
        "w": content_w - 2 * margin,
        "h": max(0, h - shelf_y - margin),
    }

    shelf_label_h = hint_line_h + 6
    tile_gap = max(8, w // 120)
    # Fit ~2 shelves of vertical space; tile height drives the rest.
    avail = shelf_area["h"]
    tile_h = max(48, int((avail - shelf_label_h - tile_gap) * 0.62))
    tile_w = tile_h * 2 // 3
    shelf_stride = tile_h + shelf_label_h + tile_gap

    # Hero portrait cover scaled to fit hero height with padding.
    cover_h = max(48, hero["h"] - 2 * margin)
    cover_w = cover_h * 2 // 3

    return {
        "rail_w": rail_w,
        "content_x": content_x,
        "margin": margin,
        "hero": hero,
        "shelf_area": shelf_area,
        "tile_w": tile_w,
        "tile_h": tile_h,
        "tile_gap": tile_gap,
        "shelf_label_h": shelf_label_h,
        "shelf_stride": shelf_stride,
        "cover_w": cover_w,
        "cover_h": cover_h,
    }
