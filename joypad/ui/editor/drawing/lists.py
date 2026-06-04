"""Game list and pick-game screens."""

import pygame

from joypad.input.profiles import game_remap_key, get_assigned_profile_id
from joypad.ui.editor.drawing.header import draw_header


def draw_game_list(session, w, h):
    draw_header(
        session,
        "Controller mapping",
        "A: edit / add   B: back   X: remove game from list",
        w,
    )
    margin = max(40, w // 20)
    list_w = min(w - margin * 2, 900)
    list_x = (w - list_w) // 2
    y0 = session.font_title.get_linesize() + session.font_hint.get_linesize() + 48
    if not session.remapped:
        msg = session.font_list.render("No games yet — press A to add", True, session.text)
        session.screen.blit(msg, (list_x, y0))
        return
    line_h = session.font_list.get_linesize() + 10
    for i, g in enumerate(session.remapped):
        y = y0 + i * line_h
        if y > h - 80:
            break
        name = g.get("name") or game_remap_key(g)
        pid = get_assigned_profile_id(session.config, g)
        label = "%s  →  %s" % (name, pid)
        if i == session.game_index:
            pygame.draw.rect(session.screen, session.highlight, (list_x - 8, y - 4, list_w + 16, line_h - 2), 1)
        surf = session.font_list.render(label, True, session.text)
        session.screen.blit(surf, (list_x, y))


def draw_pick_game(session, w, h):
    draw_header(session, "Add game", "A: assign mapping   B: cancel", w)
    margin = max(40, w // 20)
    list_w = min(w - margin * 2, 900)
    list_x = (w - list_w) // 2
    y0 = session.font_title.get_linesize() + session.font_hint.get_linesize() + 48
    line_h = session.font_list.get_linesize() + 8
    visible = max(1, (h - y0 - 60) // line_h)
    start = max(0, min(session.pick_index - visible // 2, len(session.pick_candidates) - visible))
    for row, gi in enumerate(range(start, min(len(session.pick_candidates), start + visible))):
        g = session.pick_candidates[gi]
        y = y0 + row * line_h
        sel = gi == session.pick_index
        if sel:
            pygame.draw.rect(session.screen, session.highlight, (list_x - 8, y - 4, list_w + 16, line_h - 2), 1)
        label = "%s (%s)" % (g.get("name", "?"), g.get("platform", "?"))
        surf = session.font_list.render(label, True, session.text)
        session.screen.blit(surf, (list_x, y))
