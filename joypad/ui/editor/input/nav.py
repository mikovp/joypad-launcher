"""Editor list and slot navigation."""

from joypad.ui.editor.input.constants import EDITOR_H_GROUPS


def editor_h_group(session, slot_index: int) -> tuple[int, list[int]]:
    for gi, group in enumerate(EDITOR_H_GROUPS):
        if slot_index in group:
            return gi, group
    return 0, [slot_index]


def nav_h(session, delta: int) -> None:
    if session.mode != "editor" or not session.slots:
        return
    gi, group = editor_h_group(session, session.slot_index)
    new_gi = (gi + delta) % len(EDITOR_H_GROUPS)
    new_group = EDITOR_H_GROUPS[new_gi]
    if session.slot_index in new_group:
        return
    session.slot_index = new_group[0]
    session._snap_grid_scroll()


def nav(session, delta: int) -> None:
    if session.mode == "game_list":
        if not session.remapped:
            return
        session.game_index = (session.game_index + delta) % len(session.remapped)
    elif session.mode == "pick_game":
        if not session.pick_candidates:
            return
        session.pick_index = (session.pick_index + delta) % len(session.pick_candidates)
    elif session.mode == "editor":
        n = len(session.slots)
        if n == 0:
            return
        session.slot_index = (session.slot_index + delta) % n
        session._snap_grid_scroll()
