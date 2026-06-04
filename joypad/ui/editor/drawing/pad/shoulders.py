"""Shoulder button and trigger panel rendering."""

import pygame

from joypad.input.constants import BTN_BACK, BTN_LB, BTN_RB, BTN_START
from joypad.ui.editor.slots import OUTLINE_COLOR, PANEL_SEL, _slot_display, _slot_index, _truncate_text


def draw_shoulder_panels(session, areas):
    panel_w = max(176, min(210, int(areas["content_w"] * 0.16)))
    row_h = session.font_list.get_linesize() + session.font_hint.get_linesize() + 18
    left_x = areas["content_x"] + 6
    right_x = areas["content_x"] + areas["content_w"] - panel_w - 6
    top_y = areas["pad_top"] + 6
    bot_y = areas["pad_top"] + areas["pad_h"] - row_h - 8

    left_top = [
        ("Left bumper", _slot_index(session.slots, "button", str(BTN_LB)), "LB"),
        ("Left trigger", _slot_index(session.slots, "trigger", "left"), "LT"),
    ]
    right_top = [
        ("Right bumper", _slot_index(session.slots, "button", str(BTN_RB)), "RB"),
        ("Right trigger", _slot_index(session.slots, "trigger", "right"), "RT"),
    ]
    for i, (title, idx, badge) in enumerate(left_top):
        draw_shoulder_row(session, left_x, top_y + i * row_h, panel_w, row_h, title, idx, badge, "left")
    for i, (title, idx, badge) in enumerate(right_top):
        draw_shoulder_row(session, right_x, top_y + i * row_h, panel_w, row_h, title, idx, badge, "right")

    draw_shoulder_row(
        session, left_x, bot_y, panel_w, row_h, "Back",
        _slot_index(session.slots, "button", str(BTN_BACK)), "View", "left",
    )
    draw_shoulder_row(
        session, right_x, bot_y, panel_w, row_h, "Start",
        _slot_index(session.slots, "button", str(BTN_START)), "Menu", "right",
    )


def draw_shoulder_row(session, x, y, w, h, title, slot_i, badge, side):
    if slot_i is None:
        return
    slot = session.slots[slot_i]
    selected = slot_i == session.slot_index
    if selected:
        pygame.draw.rect(session.screen, PANEL_SEL, (x, y, w, h - 2), border_radius=6)
    pygame.draw.rect(session.screen, OUTLINE_COLOR if selected else (60, 64, 78), (x, y, w, h - 2), 1, border_radius=6)

    badge_s = session.font_hint.render(badge, True, session.title)
    badge_pad = 10

    if side == "left":
        badge_x = x + w - badge_pad - badge_s.get_width()
        text_right = badge_x - 8
        text_left = x + badge_pad
        text_w = max(20, text_right - text_left)
    else:
        badge_x = x + badge_pad
        text_left = badge_x + badge_s.get_width() + 8
        text_right = x + w - badge_pad
        text_w = max(20, text_right - text_left)

    title_txt = _truncate_text(session.font_list, title, text_w)
    title_s = session.font_list.render(title_txt, True, session.text if not selected else session.highlight)
    val_txt = _truncate_text(session.font_hint, _slot_display(slot), text_w)
    val_s = session.font_hint.render(val_txt, True, session.title)

    if side == "left":
        title_x = text_left
        val_x = text_left
    else:
        title_x = text_right - title_s.get_width()
        val_x = text_right - val_s.get_width()

    session.screen.blit(badge_s, (badge_x, y + 8))
    session.screen.blit(title_s, (title_x, y + 8))
    session.screen.blit(val_s, (val_x, y + h - val_s.get_height() - 10))
