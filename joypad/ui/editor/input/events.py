"""Keyboard/gamepad event dispatch for remap editor."""

from __future__ import annotations

from typing import Callable

import pygame

from joypad.ui.editor.input.actions import back, confirm, remove_selected_game
from joypad.ui.editor.input.nav import nav, nav_h


def process_events(session, events, axis_nav: Callable[[Callable[[int], None]], None] | None = None) -> bool:
    """Handle pygame events. axis_nav: callable(delta) for stick nav."""
    for event in events:
        if event.type == pygame.QUIT:
            session.finished = True
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                back(session)
            elif event.key in (pygame.K_UP,):
                nav(session, -1)
            elif event.key in (pygame.K_DOWN,):
                nav(session, 1)
            elif event.key in (pygame.K_LEFT,) and session.mode == "editor":
                nav_h(session, -1)
            elif event.key in (pygame.K_RIGHT,) and session.mode == "editor":
                nav_h(session, 1)
            elif event.key == pygame.K_RETURN:
                confirm(session)
            elif event.key == pygame.K_DELETE and session.mode == "game_list":
                remove_selected_game(session)
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 1 or event.button == 6:
                back(session)
            elif event.button == 0 or event.button == 7:
                confirm(session)
            elif event.button == 2 and session.mode == "editor":
                session._reset_slot()
            elif event.button == 3 and session.mode == "game_list":
                remove_selected_game(session)
            elif event.button == 4 and session.mode == "editor":
                nav_h(session, -1)
            elif event.button == 5 and session.mode == "editor":
                nav_h(session, 1)
        if event.type == pygame.JOYAXISMOTION and session.mode == "editor":
            if event.axis == 5 and event.value > 0.72:
                if session._trig_arm_rt:
                    session.scroll_grid(1)
                    session._trig_arm_rt = False
            elif event.axis == 5 and event.value < 0.2:
                session._trig_arm_rt = True
            if event.axis == 4 and event.value > 0.72:
                if session._trig_arm_lt:
                    session.scroll_grid(-1)
                    session._trig_arm_lt = False
            elif event.axis == 4 and event.value < 0.2:
                session._trig_arm_lt = True
        if event.type == pygame.JOYHATMOTION and event.hat == 0:
            if session.mode == "editor":
                if event.value[0] < 0:
                    nav_h(session, -1)
                elif event.value[0] > 0:
                    nav_h(session, 1)
                elif event.value[1] > 0:
                    nav(session, -1)
                elif event.value[1] < 0:
                    nav(session, 1)
            else:
                if event.value[1] > 0:
                    nav(session, -1)
                elif event.value[1] < 0:
                    nav(session, 1)
    if axis_nav:
        axis_nav(lambda delta: nav(session, delta))
    return bool(session.finished)
