"""Main launcher event dispatch (keyboard, gamepad)."""

from __future__ import annotations

from typing import Callable

import pygame

from joypad.input.constants import (
    AXIS_LEFT_X,
    AXIS_LEFT_Y,
    AXIS_REPEAT_FRAMES,
    BTN_A,
    BTN_B,
    BTN_BACK,
    BTN_LB,
    BTN_RB,
    BTN_START,
    DEADZONE,
)
from joypad.ui import overlay as ovl
from joypad.ui.loop.context import LoopContext
from joypad.ui.views import home as hm
from joypad.ui.views import list as lst


def _home_confirm(state, on_launch):
    """home_confirm, then finalize a rail-triggered settings open the canonical way."""
    prev = state.overlay_menu
    launched = hm.home_confirm(state, on_launch)
    if state.overlay_menu == "settings" and prev != "settings":
        ovl.open_settings_overlay(state)
    return launched


def process_events(
    state,
    events,
    ctx: LoopContext,
    joysticks: list,
    on_launch: Callable[[], bool],
    *,
    use_xinput_gamepad: bool = False,
) -> tuple[list, bool]:
    """Handle pygame events. Returns updated joysticks and whether to exit the app."""
    from joypad.ui.loop.joysticks import rescan_joysticks

    menu_back_handled = False
    skip_gamepad = use_xinput_gamepad

    for event in events:
        if event.type == pygame.QUIT:
            state.running = False
        if event.type == getattr(pygame, "JOYDEVICEADDED", None):
            joysticks = rescan_joysticks()
        if event.type == pygame.KEYDOWN:
            if state.overlay_menu:
                if event.key == pygame.K_ESCAPE:
                    ovl.overlay_back(state)
                if event.key == pygame.K_UP:
                    ovl.overlay_move(state, -1)
                if event.key == pygame.K_DOWN:
                    ovl.overlay_move(state, 1)
                if event.key == pygame.K_RETURN:
                    ovl.overlay_confirm(state)
            else:
                if event.key == pygame.K_ESCAPE:
                    state.overlay_menu = "system"
                    state.overlay_index = 0
                if event.key == pygame.K_UP:
                    lst.nav_vertical(state, -1)
                if event.key == pygame.K_DOWN:
                    lst.nav_vertical(state, 1)
                if event.key == pygame.K_LEFT:
                    lst.nav_horizontal(state, -1)
                if event.key == pygame.K_RIGHT:
                    lst.nav_horizontal(state, 1)
                if event.key == pygame.K_PAGEUP:
                    lst.nav_page(state, -1)
                if event.key == pygame.K_PAGEDOWN:
                    lst.nav_page(state, 1)
                if event.key == pygame.K_RETURN:
                    launched = _home_confirm(state, on_launch) if state.ui_mode == "home" else on_launch()
                    if launched:
                        state.running = False
                        return joysticks, True

        if event.type == pygame.JOYBUTTONDOWN:
            if skip_gamepad:
                continue
            btn = event.button
            if btn == BTN_B or btn == BTN_BACK:
                if menu_back_handled:
                    continue
                menu_back_handled = True
                if state.overlay_menu:
                    ovl.overlay_back(state)
                else:
                    state.overlay_menu = "system"
                    state.overlay_index = 0
                continue

            if state.overlay_menu:
                if btn == BTN_A or btn == BTN_START:
                    ovl.overlay_confirm(state)
            else:
                if btn == BTN_A or btn == BTN_START:
                    launched = _home_confirm(state, on_launch) if state.ui_mode == "home" else on_launch()
                    if launched:
                        state.running = False
                        return joysticks, True
                elif btn == BTN_LB:
                    lst.nav_lb_rb(state, -1)
                elif btn == BTN_RB:
                    lst.nav_lb_rb(state, 1)

        if event.type == pygame.JOYAXISMOTION and event.axis == AXIS_LEFT_Y:
            if skip_gamepad:
                continue
            if ctx.axis_held <= 0:
                if state.overlay_menu:
                    if event.value < -DEADZONE:
                        ovl.overlay_move(state, -1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                    elif event.value > DEADZONE:
                        ovl.overlay_move(state, 1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                else:
                    if event.value < -DEADZONE:
                        lst.nav_vertical(state, -1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                    elif event.value > DEADZONE:
                        lst.nav_vertical(state, 1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
        elif event.type == pygame.JOYAXISMOTION and event.axis == AXIS_LEFT_X:
            if skip_gamepad:
                continue
            if not state.overlay_menu and ctx.axis_held <= 0:
                if event.value < -DEADZONE:
                    lst.nav_horizontal(state, -1)
                    ctx.axis_held = AXIS_REPEAT_FRAMES
                elif event.value > DEADZONE:
                    lst.nav_horizontal(state, 1)
                    ctx.axis_held = AXIS_REPEAT_FRAMES
        elif event.type == pygame.JOYAXISMOTION:
            if skip_gamepad:
                continue
            if not state.overlay_menu and ctx.axis_held <= 0:
                if event.axis == 5 and event.value > 0.72:
                    if ctx.trig_page_arm_rt:
                        lst.nav_page(state, 1)
                        ctx.trig_page_arm_rt = False
                        ctx.axis_held = AXIS_REPEAT_FRAMES * 2
                elif event.axis == 5 and event.value < 0.2:
                    ctx.trig_page_arm_rt = True
                if event.axis == 4 and event.value > 0.72:
                    if ctx.trig_page_arm_lt:
                        lst.nav_page(state, -1)
                        ctx.trig_page_arm_lt = False
                        ctx.axis_held = AXIS_REPEAT_FRAMES * 2
                elif event.axis == 4 and event.value < 0.2:
                    ctx.trig_page_arm_lt = True
        if event.type == pygame.JOYHATMOTION and event.hat == 0:
            if skip_gamepad:
                continue
            if ctx.axis_held <= 0:
                if state.overlay_menu:
                    if event.value[1] > 0:
                        ovl.overlay_move(state, -1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                    elif event.value[1] < 0:
                        ovl.overlay_move(state, 1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                else:
                    if event.value[1] > 0:
                        lst.nav_vertical(state, -1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                    elif event.value[1] < 0:
                        lst.nav_vertical(state, 1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                    if event.value[0] < 0:
                        lst.nav_horizontal(state, -1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES
                    elif event.value[0] > 0:
                        lst.nav_horizontal(state, 1)
                        ctx.axis_held = AXIS_REPEAT_FRAMES

    return joysticks, False
