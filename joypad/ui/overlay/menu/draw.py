"""Render system and settings overlay menus."""

import pygame

from joypad.ui.overlay.menu.layout import overlay_items


def draw_overlay(state):
    """Render the system or settings overlay menu."""
    if not state.overlay_menu:
        return

    screen = state.screen
    w, h = state.w, state.h
    menu_width = min(w - 80, 860)
    header_h = 48
    max_menu_h = max(120, h - 80)
    max_overlay_scroll = 0
    overlay_scroll_y_clamped = 0
    menu_x = 0
    menu_y = 0
    body_top = 0
    body_h = 0

    if state.overlay_menu == "settings":
        content_h = state.settings_content_h
        menu_height = min(content_h + header_h, max_menu_h)
        body_h = menu_height - header_h
        max_overlay_scroll = max(0, content_h - body_h)
        overlay_scroll_y_clamped = max(0, min(state.overlay_scroll_y, max_overlay_scroll))
        menu_x = (w - menu_width) // 2
        menu_y = (h - menu_height) // 2 - 10

        pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(screen, state.title_color, (menu_x, menu_y, menu_width, menu_height), 2)

        menu_title = state.font_title.render("Settings", True, state.title_color)
        title_x = menu_x + (menu_width - menu_title.get_width()) // 2
        screen.blit(menu_title, (title_x, menu_y + 8))

        body_top = menu_y + header_h
        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(menu_x, body_top, menu_width, body_h))
        try:
            for idx, spec in enumerate(state.settings_row_specs):
                y_content = state.settings_cum_starts[idx]
                rh = spec["height"]
                row_y = body_top + y_content - overlay_scroll_y_clamped
                if row_y + rh < body_top or row_y > body_top + body_h:
                    continue
                if spec["kind"] == "header":
                    text = state.font_category.render("  %s" % spec["title"], True, state.title_color)
                    screen.blit(text, (menu_x + 20, row_y))
                else:
                    item = spec["item"]
                    color = state.highlight_color if idx == state.overlay_index else state.text_color
                    text = state.font_list.render(item["label"], True, color)
                    row_x = menu_x + max(20, (menu_width - text.get_width()) // 2)
                    screen.blit(text, (row_x, row_y))
        finally:
            screen.set_clip(prev_clip)
    else:
        items = overlay_items(state)
        menu_line_h = state.font_list.get_linesize() + 8
        content_h = len(items) * menu_line_h
        menu_height = min(content_h + header_h, max_menu_h)
        body_h = menu_height - header_h
        max_overlay_scroll = max(0, content_h - body_h)
        overlay_scroll_y_clamped = max(0, min(state.overlay_scroll_y, max_overlay_scroll))
        menu_x = (w - menu_width) // 2
        menu_y = (h - menu_height) // 2 - 10

        pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(screen, state.title_color, (menu_x, menu_y, menu_width, menu_height), 2)

        menu_title = state.font_title.render("System menu", True, state.title_color)
        title_x = menu_x + (menu_width - menu_title.get_width()) // 2
        screen.blit(menu_title, (title_x, menu_y + 8))

        body_top = menu_y + header_h
        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(menu_x, body_top, menu_width, body_h))
        try:
            for idx, item in enumerate(items):
                color = state.highlight_color if idx == state.overlay_index else state.text_color
                text = state.font_list.render(item["label"], True, color)
                row_y = body_top + idx * menu_line_h - overlay_scroll_y_clamped
                if row_y + menu_line_h < body_top or row_y > body_top + body_h:
                    continue
                row_x = menu_x + max(20, (menu_width - text.get_width()) // 2)
                screen.blit(text, (row_x, row_y))
        finally:
            screen.set_clip(prev_clip)

    if max_overlay_scroll > 0:
        if overlay_scroll_y_clamped > 0:
            up_arrow = state.font_list.render(" ▲", True, state.title_color)
            screen.blit(up_arrow, (menu_x + menu_width - 36, body_top + 2))
        if overlay_scroll_y_clamped < max_overlay_scroll:
            down_arrow = state.font_list.render(" ▼", True, state.title_color)
            screen.blit(down_arrow, (menu_x + menu_width - 36, body_top + body_h - state.font_list.get_linesize() - 2))
