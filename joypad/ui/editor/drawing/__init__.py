"""Pygame rendering for the input remap editor."""

from joypad.ui.editor.drawing import grid, lists, pad
from joypad.ui.editor.drawing.header import draw_header
from joypad.ui.editor.layout import editor_areas
from joypad.ui.editor.slots import PAD_IMAGE_ASPECT


def draw(session):
    w, h = session.screen.get_size()
    session.screen.fill(session.bg)
    if session.mode == "game_list":
        lists.draw_game_list(session, w, h)
    elif session.mode == "pick_game":
        lists.draw_pick_game(session, w, h)
    else:
        draw_editor(session, w, h)


def draw_editor(session, w, h):
    game_name = (session.current_game or {}).get("name") or "Game"
    draw_header(
        session,
        "Controller mapping: %s" % game_name,
        "↑↓ element   ←→ group   LT/RT FACE scroll   A +/change   X −/clear   B back",
        w,
    )
    areas = editor_areas(session, w, h)
    img_h = int(areas["pad_h"] * 0.88)
    img_w = int(img_h * PAD_IMAGE_ASPECT)
    img_w = min(img_w, int(areas["content_w"] * 0.62))
    pad_img = pad.get_gamepad_image(session, img_w, img_h)
    if pad_img:
        rect = pad_img.get_rect(center=(areas["cx"], areas["cy"]))
        session.screen.blit(pad_img, rect)
        pad.draw_pad_highlight(session, areas["cx"], areas["cy"], img_w, img_h)
    else:
        bw = min(int(areas["pad_h"] * 1.55), int(areas["content_w"] * 0.34), 420)
        bh = int(areas["pad_h"] * 0.62)
        pad.draw_controller_wireframe(session, areas["cx"], areas["cy"], bw, bh)
    pad.draw_shoulder_panels(session, areas)
    grid.draw_mapping_grid(session, areas)
    grid.draw_editor_footer(session, w, areas["footer_y"])
