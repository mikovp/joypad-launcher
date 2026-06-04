"""Editor layout geometry (areas, grid metrics)."""


def grid_header_h(session):
    return 6 + session.font_list.get_linesize() + 6


def editor_areas(session, w, h):
    title_h = session.font_title.get_linesize()
    hint_h = session.font_hint.get_linesize()
    header_h = 20 + title_h + 6 + hint_h + 12
    footer_h = 36
    line_h = session.font_list.get_linesize() + 5
    face_line_h = session.font_list.get_linesize() + 2
    settings_band = line_h * 2 + 18
    body_h = h - header_h - footer_h
    pad_h = max(120, int(body_h * 0.41))
    grid_h = body_h - pad_h - 8
    grid_rows_h = max(100, grid_h - settings_band)
    margin = max(24, w // 40)
    content_w = min(w - margin * 2, 1180)
    content_x = (w - content_w) // 2
    grid_top = header_h + pad_h + 8
    return {
        "header_h": header_h,
        "pad_top": header_h,
        "pad_h": pad_h,
        "grid_top": grid_top,
        "grid_h": grid_h,
        "grid_rows_h": grid_rows_h,
        "settings_y": grid_top + grid_rows_h + 4,
        "line_h": line_h,
        "face_line_h": face_line_h,
        "footer_y": h - footer_h,
        "content_x": content_x,
        "content_w": content_w,
        "cx": w // 2,
        "cy": header_h + pad_h // 2,
    }
