"""Editor confirm, back, and game removal."""

from joypad.input.profiles import (
    assign_game_profile,
    save_profile,
    suggest_profile_id,
    unassign_game,
)


def confirm(session) -> None:
    if session.mode == "game_list":
        if not session.remapped:
            session.mode = "pick_game"
            session.pick_index = 0
            return
        session._load_editor_for_game(session.remapped[session.game_index])
    elif session.mode == "pick_game":
        if not session.pick_candidates:
            return
        game = session.pick_candidates[session.pick_index]
        pid = suggest_profile_id(game)
        assign_game_profile(session.config, game, pid, session.base_dir)
        session.save_config(session.config)
        session._refresh_game_list()
        session._load_editor_for_game(game)
    elif session.mode == "editor":
        session._cycle_current_slot()


def back(session) -> None:
    if session.mode == "editor":
        save_profile(session.profile_path, session.profile)
        session.mode = "game_list"
        session._refresh_game_list()
    elif session.mode == "pick_game":
        session.mode = "game_list"
    else:
        session.finished = True


def remove_selected_game(session) -> None:
    if session.mode != "game_list" or not session.remapped:
        return
    unassign_game(session.config, session.remapped[session.game_index])
    session.save_config(session.config)
    session._refresh_game_list()
