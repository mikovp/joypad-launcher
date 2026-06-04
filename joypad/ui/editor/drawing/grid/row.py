"""Single mapping grid row rendering."""

import pygame

from joypad.ui.editor.slots import PANEL_SEL, _slot_display, _truncate_text


def draw_grid_row(session, x, y, w, h, label, slot_i, badge_color=None):
    slot = session.slots[slot_i]
    selected = slot_i == session.slot_index
    if selected:
        pygame.draw.rect(session.screen, PANEL_SEL, (x - 4, y - 2, w + 8, h + 2), border_radius=4)

    lx = x + (22 if badge_color else 0)
    inner_w = w - (22 if badge_color else 0)
    if badge_color:
        pygame.draw.circle(session.screen, badge_color, (x + 9, y + h // 2), 7)

    label_s = session.font_list.render(
        _truncate_text(session.font_list, label, inner_w // 2),
        True,
        session.text if not selected else session.highlight,
    )
    val_s = session.font_list.render(
        _slot_display(slot),
        True,
        session.highlight if selected else session.title,
    )
    val_x = x + w - val_s.get_width()
    label_max = max(20, val_x - lx - 10)
    if label_s.get_width() > label_max:
        label_s = session.font_list.render(
            _truncate_text(session.font_list, label, label_max),
            True,
            session.text if not selected else session.highlight,
        )
    session.screen.blit(label_s, (lx, y + 1))
    session.screen.blit(val_s, (val_x, y + 1))
