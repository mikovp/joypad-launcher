"""List view pygame rendering."""

import pygame


def footer_line_count(state):
    """Footer hint lines (controls only)."""
    return 2


def _compose_footer_surface(state, lines):
    surfaces = [state.font_hint.render(line, True, state.title_color) for line in lines]
    if not surfaces:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    width = max(s.get_width() for s in surfaces)
    gap = 2
    height = sum(s.get_height() for s in surfaces) + gap * (len(surfaces) - 1)
    combined = pygame.Surface((width, height), pygame.SRCALPHA)
    y = 0
    for surf in surfaces:
        combined.blit(surf, (0, y))
        y += surf.get_height() + gap
    return combined


def _hint_surfaces(state):
    if state.ui_mode == "tiles":
        title = state.font_hint.render("Pick a game (tiles)", True, state.title_color)
        controls = "A — launch   B — menu   ←→↑↓   LB/RB — library (1st tile)   LT/RT — scroll"
    else:
        title = state.font_hint.render("Select a game or action (gamepad or keyboard)", True, state.title_color)
        controls = "A / Enter — launch   B / Esc — menu   ↑↓ row   PgUp/PgDn   LB/RB   LT/RT — page"

    footer_lines = [controls]
    hint = _compose_footer_surface(state, footer_lines)
    return title, hint


def draw_list_view(state):
    """Render the categorized game list with scroll indicators."""
    screen = state.screen
    w = state.w
    scroll_y = state.list_scroll_y
    prev_clip = screen.get_clip()
    screen.set_clip(pygame.Rect(0, state.list_start_y, w, state.viewport_h))
    try:
        for idx in range(len(state.list_items)):
            y_content = state.cum_starts[idx]
            rh = state.row_specs[idx]["height"]
            screen_y = state.list_start_y + y_content - scroll_y
            if screen_y + rh < state.list_start_y or screen_y > state.list_start_y + state.viewport_h:
                continue
            spec = state.row_specs[idx]
            if spec["kind"] == "header":
                text = state.font_category.render("  %s" % spec["title"], True, state.title_color)
                screen.blit(text, (60, screen_y))
            else:
                color = state.highlight_color if idx == state.selected else state.text_color
                screen.blit(state.font_list.render(spec["prefix"], True, color), (state.list_left, screen_y))
                ly = screen_y
                for chunk in spec["name_lines"]:
                    surf = state.font_list.render(chunk, True, color)
                    screen.blit(surf, (spec["x_text"], ly))
                    ly += state.list_line_skip
    finally:
        screen.set_clip(prev_clip)

    if state.max_scroll_y > 0:
        if scroll_y > 0:
            up_arrow = state.font_list.render(" ▲", True, state.title_color)
            screen.blit(up_arrow, (w - 50, state.list_start_y + 4))
        if scroll_y < state.max_scroll_y:
            down_arrow = state.font_list.render(" ▼", True, state.title_color)
            screen.blit(
                down_arrow,
                (w - 50, state.list_start_y + state.viewport_h - state.font_list.get_linesize() - 4),
            )
