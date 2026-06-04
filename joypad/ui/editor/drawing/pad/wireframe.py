"""Gamepad wireframe and slot highlight rendering."""

import pygame

from joypad.ui.editor.slots import OUTLINE_COLOR, PAD_RADIUS, _pad_hotspot, _slot_index


def draw_pad_highlight(session, cx, cy, iw, ih):
    if not session.slots:
        return
    slot = session.slots[session.slot_index]
    hit = _pad_hotspot(slot)
    if not hit:
        return
    (nx, ny), rkey = hit
    px = cx - iw // 2 + int(nx * iw)
    py = cy - ih // 2 + int(ny * ih)
    r = max(10, int(iw * PAD_RADIUS.get(rkey, 0.045)))
    pygame.draw.circle(session.screen, session.highlight, (px, py), r + 4, 3)
    pygame.draw.circle(session.screen, session.highlight, (px, py), max(6, r - 6), 1)


def draw_controller_wireframe(session, cx, cy, bw, bh):
    o = OUTLINE_COLOR
    hw, hh = bw // 2, bh // 2
    body = pygame.Rect(cx - hw, cy - hh + hh // 5, bw, int(bh * 0.78))
    pygame.draw.ellipse(session.screen, o, body, 2)
    grip_l = pygame.Rect(cx - hw - int(bw * 0.08), cy - int(hh * 0.15), int(bw * 0.38), int(bh * 0.72))
    grip_r = pygame.Rect(cx + hw - int(bw * 0.30), cy - int(hh * 0.15), int(bw * 0.38), int(bh * 0.72))
    pygame.draw.ellipse(session.screen, o, grip_l, 2)
    pygame.draw.ellipse(session.screen, o, grip_r, 2)

    ls_x = cx - int(bw * 0.20)
    ls_y = cy + int(bh * 0.06)
    rs_x = cx + int(bw * 0.18)
    rs_y = cy + int(bh * 0.14)
    lr = max(16, int(bw * 0.09))
    rr = max(14, int(bw * 0.08))
    for x, y, r in ((ls_x, ls_y, lr), (rs_x, rs_y, rr)):
        pygame.draw.circle(session.screen, o, (x, y), r, 2)
        pygame.draw.circle(session.screen, o, (x, y), max(6, r - 8), 2)

    dp_x = cx - int(bw * 0.34)
    dp_y = cy + int(bh * 0.20)
    d = max(8, int(bw * 0.035))
    pygame.draw.rect(session.screen, o, (dp_x - d, dp_y - d * 3, d * 2, d * 2), 2)
    pygame.draw.rect(session.screen, o, (dp_x - d, dp_y + d, d * 2, d * 2), 2)
    pygame.draw.rect(session.screen, o, (dp_x - d * 3, dp_y - d, d * 2, d * 2), 2)
    pygame.draw.rect(session.screen, o, (dp_x + d, dp_y - d, d * 2, d * 2), 2)

    fx = cx + int(bw * 0.30)
    fy = cy + int(bh * 0.02)
    off = max(10, int(bw * 0.045))
    btn_r = max(8, int(bw * 0.038))
    for dx, dy in ((0, -off), (off, 0), (0, off), (-off, 0)):
        pygame.draw.circle(session.screen, o, (fx + dx, fy + dy), btn_r, 2)

    xb_y = cy - int(bh * 0.12)
    pygame.draw.circle(session.screen, o, (cx, xb_y), max(7, int(bw * 0.035)), 2)

    li = _slot_index(session.slots, "left_stick")
    ri = _slot_index(session.slots, "right_stick")
    if session.slot_index == li:
        pygame.draw.circle(session.screen, session.highlight, (ls_x, ls_y), lr + 4, 2)
    if session.slot_index == ri:
        pygame.draw.circle(session.screen, session.highlight, (rs_x, rs_y), rr + 4, 2)
