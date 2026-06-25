"""Tests for main-loop event dispatch (keyboard, gamepad, axes, hat)."""

from types import SimpleNamespace

import pygame
import pytest

from joypad.bootstrap.constants import SYSTEM_MENU_ITEMS
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
from joypad.ui.loop.context import LoopContext
from joypad.ui.loop.events.dispatch import process_events


def _key_event(key):
    return SimpleNamespace(type=pygame.KEYDOWN, key=key)


def _btn_event(button):
    return SimpleNamespace(type=pygame.JOYBUTTONDOWN, button=button)


def _axis_event(axis, value):
    return SimpleNamespace(type=pygame.JOYAXISMOTION, axis=axis, value=value)


def _hat_event(x, y):
    return SimpleNamespace(type=pygame.JOYHATMOTION, hat=0, value=(x, y))


def _state(overlay_menu=None, overlay_index=0):
    return SimpleNamespace(
        overlay_menu=overlay_menu,
        overlay_index=overlay_index,
        overlay_scroll_y=0,
        running=True,
        system_menu_items=list(SYSTEM_MENU_ITEMS),
        settings_menu_items=[],
        ui_mode="list",
    )


def _run(state, events, ctx=None, on_launch=lambda: False):
    ctx = ctx or LoopContext()
    return process_events(state, events, ctx, [], on_launch)


@pytest.fixture
def nav_calls(monkeypatch):
    calls = []

    def record(name):
        def _fn(state, delta):
            calls.append((name, delta))

        return _fn

    monkeypatch.setattr(
        "joypad.ui.loop.events.dispatch.lst.nav_vertical", record("nav_vertical")
    )
    monkeypatch.setattr(
        "joypad.ui.loop.events.dispatch.lst.nav_horizontal", record("nav_horizontal")
    )
    monkeypatch.setattr(
        "joypad.ui.loop.events.dispatch.lst.nav_page", record("nav_page")
    )
    monkeypatch.setattr(
        "joypad.ui.loop.events.dispatch.lst.nav_lb_rb", record("nav_lb_rb")
    )
    return calls


@pytest.fixture
def overlay_calls(monkeypatch):
    calls = []

    def move(state, delta):
        calls.append(("overlay_move", delta))
        state.overlay_index = (state.overlay_index + delta) % len(state.system_menu_items)

    def confirm(state):
        calls.append("overlay_confirm")
        item = state.system_menu_items[state.overlay_index]
        if item["key"] == "resume":
            state.overlay_menu = None

    monkeypatch.setattr("joypad.ui.loop.events.dispatch.ovl.overlay_move", move)
    monkeypatch.setattr("joypad.ui.loop.events.dispatch.ovl.overlay_confirm", confirm)
    monkeypatch.setattr("joypad.ui.loop.events.dispatch.ovl.overlay_back", lambda state: setattr(state, "overlay_menu", None))
    return calls


# --- Keyboard (main view) ---


@pytest.mark.parametrize(
    "key,expected",
    [
        (pygame.K_UP, ("nav_vertical", -1)),
        (pygame.K_DOWN, ("nav_vertical", 1)),
        (pygame.K_LEFT, ("nav_horizontal", -1)),
        (pygame.K_RIGHT, ("nav_horizontal", 1)),
        (pygame.K_PAGEUP, ("nav_page", -1)),
        (pygame.K_PAGEDOWN, ("nav_page", 1)),
    ],
)
def test_keyboard_main_view_navigation(key, expected, nav_calls):
    state = _state()
    _run(state, [_key_event(key)])
    assert nav_calls == [expected]


def test_keyboard_escape_opens_system_menu():
    state = _state()
    _run(state, [_key_event(pygame.K_ESCAPE)])
    assert state.overlay_menu == "system"
    assert state.overlay_index == 0


def test_keyboard_return_launches_when_on_launch_true():
    state = _state()
    _, should_exit = _run(state, [_key_event(pygame.K_RETURN)], on_launch=lambda: True)
    assert should_exit is True
    assert state.running is False


def test_keyboard_return_does_not_exit_when_on_launch_false():
    state = _state()
    _, should_exit = _run(state, [_key_event(pygame.K_RETURN)], on_launch=lambda: False)
    assert should_exit is False
    assert state.running is True


# --- Keyboard (overlay) ---


@pytest.mark.parametrize(
    "key,expected",
    [
        (pygame.K_UP, ("overlay_move", -1)),
        (pygame.K_DOWN, ("overlay_move", 1)),
    ],
)
def test_keyboard_overlay_navigation(key, expected, overlay_calls):
    state = _state(overlay_menu="system")
    _run(state, [_key_event(key)])
    assert overlay_calls == [expected]


def test_keyboard_escape_closes_overlay(overlay_calls):
    state = _state(overlay_menu="system")
    _run(state, [_key_event(pygame.K_ESCAPE)])
    assert state.overlay_menu is None


def test_keyboard_return_confirms_overlay(overlay_calls):
    state = _state(overlay_menu="system", overlay_index=0)
    _run(state, [_key_event(pygame.K_RETURN)])
    assert overlay_calls == ["overlay_confirm"]
    assert state.overlay_menu is None


# --- Gamepad buttons (main view) ---


@pytest.mark.parametrize("button", [BTN_B, BTN_BACK])
def test_gamepad_back_opens_system_menu(button):
    state = _state()
    _run(state, [_btn_event(button)])
    assert state.overlay_menu == "system"
    assert state.overlay_index == 0


def test_duplicate_back_events_in_one_batch_open_menu_once():
    state = _state()
    _run(state, [_btn_event(BTN_B), _btn_event(BTN_BACK)])
    assert state.overlay_menu == "system"


def test_duplicate_back_events_in_one_batch_close_menu_once():
    state = _state(overlay_menu="system")
    _run(state, [_btn_event(BTN_B), _btn_event(BTN_BACK)])
    assert state.overlay_menu is None


@pytest.mark.parametrize("button", [BTN_A, BTN_START])
def test_gamepad_launch_exits_when_on_launch_true(button):
    state = _state()
    _, should_exit = _run(state, [_btn_event(button)], on_launch=lambda: True)
    assert should_exit is True
    assert state.running is False


@pytest.mark.parametrize("button", [BTN_A, BTN_START])
def test_gamepad_launch_no_exit_when_on_launch_false(button):
    state = _state()
    _, should_exit = _run(state, [_btn_event(button)], on_launch=lambda: False)
    assert should_exit is False
    assert state.running is True


@pytest.mark.parametrize(
    "button,expected",
    [
        (BTN_LB, ("nav_lb_rb", -1)),
        (BTN_RB, ("nav_lb_rb", 1)),
    ],
)
def test_gamepad_bumpers_navigate_sections(button, expected, nav_calls):
    state = _state()
    _run(state, [_btn_event(button)])
    assert nav_calls == [expected]


# --- Gamepad buttons (overlay) ---


@pytest.mark.parametrize("button", [BTN_B, BTN_BACK])
def test_gamepad_back_closes_overlay(button):
    state = _state(overlay_menu="system")
    _run(state, [_btn_event(button)])
    assert state.overlay_menu is None


@pytest.mark.parametrize("button", [BTN_A, BTN_START])
def test_gamepad_confirm_in_overlay(button, overlay_calls):
    state = _state(overlay_menu="system", overlay_index=0)
    _run(state, [_btn_event(button)])
    assert overlay_calls == ["overlay_confirm"]
    assert state.overlay_menu is None


# --- Left stick ---


@pytest.mark.parametrize(
    "value,expected",
    [
        (-(DEADZONE + 0.1), ("nav_vertical", -1)),
        (DEADZONE + 0.1, ("nav_vertical", 1)),
    ],
)
def test_stick_y_main_view_navigates(value, expected, nav_calls):
    state = _state()
    ctx = LoopContext()
    _run(state, [_axis_event(AXIS_LEFT_Y, value)], ctx=ctx)
    assert nav_calls == [expected]
    assert ctx.axis_held == AXIS_REPEAT_FRAMES


@pytest.mark.parametrize(
    "value,expected",
    [
        (-(DEADZONE + 0.1), ("overlay_move", -1)),
        (DEADZONE + 0.1, ("overlay_move", 1)),
    ],
)
def test_stick_y_overlay_navigates(value, expected, overlay_calls):
    state = _state(overlay_menu="system")
    ctx = LoopContext()
    _run(state, [_axis_event(AXIS_LEFT_Y, value)], ctx=ctx)
    assert overlay_calls == [expected]
    assert ctx.axis_held == AXIS_REPEAT_FRAMES


@pytest.mark.parametrize(
    "value,expected",
    [
        (-(DEADZONE + 0.1), ("nav_horizontal", -1)),
        (DEADZONE + 0.1, ("nav_horizontal", 1)),
    ],
)
def test_stick_x_main_view_navigates(value, expected, nav_calls):
    state = _state()
    ctx = LoopContext()
    _run(state, [_axis_event(AXIS_LEFT_X, value)], ctx=ctx)
    assert nav_calls == [expected]
    assert ctx.axis_held == AXIS_REPEAT_FRAMES


def test_stick_x_ignored_in_overlay(nav_calls):
    state = _state(overlay_menu="system")
    ctx = LoopContext()
    _run(state, [_axis_event(AXIS_LEFT_X, -(DEADZONE + 0.1))], ctx=ctx)
    assert nav_calls == []
    assert ctx.axis_held == 0


def test_stick_ignored_while_axis_held(nav_calls):
    state = _state()
    ctx = LoopContext(axis_held=5)
    _run(state, [_axis_event(AXIS_LEFT_Y, -(DEADZONE + 0.1))], ctx=ctx)
    assert nav_calls == []
    assert ctx.axis_held == 5


# --- Triggers (page scroll) ---


def test_trigger_lt_pages_up(nav_calls):
    state = _state()
    ctx = LoopContext()
    _run(state, [_axis_event(4, 0.9)], ctx=ctx)
    assert nav_calls == [("nav_page", -1)]
    assert ctx.trig_page_arm_lt is False
    assert ctx.axis_held == AXIS_REPEAT_FRAMES * 2


def test_trigger_rt_pages_down(nav_calls):
    state = _state()
    ctx = LoopContext()
    _run(state, [_axis_event(5, 0.9)], ctx=ctx)
    assert nav_calls == [("nav_page", 1)]
    assert ctx.trig_page_arm_rt is False


def test_trigger_rearm_after_release(nav_calls):
    state = _state()
    ctx = LoopContext()
    _run(state, [_axis_event(4, 0.9)], ctx=ctx)
    assert nav_calls == [("nav_page", -1)]
    nav_calls.clear()
    ctx.axis_held = 0
    _run(state, [_axis_event(4, 0.9)], ctx=ctx)
    assert nav_calls == []
    _run(state, [_axis_event(4, 0.0)], ctx=ctx)
    ctx.axis_held = 0
    _run(state, [_axis_event(4, 0.9)], ctx=ctx)
    assert nav_calls == [("nav_page", -1)]


def test_triggers_ignored_in_overlay(nav_calls):
    state = _state(overlay_menu="system")
    ctx = LoopContext()
    _run(state, [_axis_event(4, 0.9), _axis_event(5, 0.9)], ctx=ctx)
    assert nav_calls == []


# --- D-pad (hat) ---


@pytest.mark.parametrize(
    "hat,expected",
    [
        ((0, 1), [("nav_vertical", -1)]),
        ((0, -1), [("nav_vertical", 1)]),
        ((-1, 0), [("nav_horizontal", -1)]),
        ((1, 0), [("nav_horizontal", 1)]),
    ],
)
def test_hat_main_view(hat, expected, nav_calls):
    state = _state()
    ctx = LoopContext()
    _run(state, [_hat_event(*hat)], ctx=ctx)
    assert nav_calls == expected
    assert ctx.axis_held == AXIS_REPEAT_FRAMES


@pytest.mark.parametrize(
    "hat,expected",
    [
        ((0, 1), [("overlay_move", -1)]),
        ((0, -1), [("overlay_move", 1)]),
    ],
)
def test_hat_overlay_vertical(hat, expected, overlay_calls):
    state = _state(overlay_menu="system")
    ctx = LoopContext()
    _run(state, [_hat_event(*hat)], ctx=ctx)
    assert overlay_calls == expected


def test_hat_diagonal_main_view_calls_both(nav_calls):
    state = _state()
    ctx = LoopContext()
    _run(state, [_hat_event(-1, 1)], ctx=ctx)
    assert ("nav_vertical", -1) in nav_calls
    assert ("nav_horizontal", -1) in nav_calls


# --- Misc ---


def test_quit_sets_running_false():
    state = _state()
    _run(state, [SimpleNamespace(type=pygame.QUIT)])
    assert state.running is False


def test_joy_device_added_rescans_joysticks(monkeypatch):
    state = _state()
    seen = []

    def fake_rescan():
        seen.append(True)
        return ["joy0"]

    monkeypatch.setattr(
        "joypad.ui.loop.joysticks.rescan_joysticks", fake_rescan
    )
    joysticks, _ = _run(
        state,
        [SimpleNamespace(type=getattr(pygame, "JOYDEVICEADDED", None))],
    )
    assert seen == [True]
    assert joysticks == ["joy0"]
