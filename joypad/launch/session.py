"""Launch session state and game-launch callbacks for the main loop."""

from __future__ import annotations

import atexit
from dataclasses import dataclass
from typing import Any, Callable

from joypad.integrations import LAUNCHABLE_PLATFORMS
from joypad.launch.launcher import try_launch_game
from joypad.ui import overlay as ovl
from joypad.ui.views import list as lst


@dataclass
class LaunchSession:
    steam_path: str | None
    default_args: dict
    steam_skip_restore_ids: set[str]
    hwnd: Any
    active_remap_proc: list


def register_remap_cleanup(active_remap_proc: list) -> Callable[[], None]:
    """Register atexit hook to stop an active remap worker subprocess."""

    def stop_active_remap():
        if active_remap_proc[0]:
            from joypad.input.worker import stop_remap_worker

            stop_remap_worker(active_remap_proc[0])
            active_remap_proc[0] = None

    atexit.register(stop_active_remap)
    return stop_active_remap


def make_on_launch(state, session: LaunchSession, loop_ctx) -> Callable[[], bool]:
    """Build the launch callback used by the input handler (returns True to exit app)."""

    def _make_launch_spinner(saved, frame_ref):
        if saved is None:
            return None

        def tick():
            frame_ref[0] = ovl.tick_launching_spinner(state, saved, frame_ref[0], sleep=False)

        return tick

    def _launch_selected():
        it = lst.get_selected_item(state)
        if not it:
            return None
        g = it["game"]
        launch_saved, launch_frame = None, [0]
        if g.get("platform") in LAUNCHABLE_PLATFORMS:
            launch_saved, launch_frame[0] = ovl.begin_launching_overlay(state, g.get("name", "Game"))
        return try_launch_game(
            g,
            state,
            steam_path=session.steam_path,
            default_args=session.default_args,
            steam_skip_restore_ids=session.steam_skip_restore_ids,
            hwnd=session.hwnd,
            active_remap_proc=session.active_remap_proc,
            spinner_tick=_make_launch_spinner(launch_saved, launch_frame),
        )

    def _on_launch():
        result = _launch_selected()
        if result is None:
            return False
        should_exit, axis_held_val = result
        loop_ctx.axis_held = axis_held_val
        return should_exit

    return _on_launch
