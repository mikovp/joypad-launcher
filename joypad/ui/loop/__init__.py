"""Main loop input handling and frame rendering."""

from joypad.ui.loop.context import RESCAN_INTERVAL, LoopContext
from joypad.ui.loop.events import get_events, handle_remap_session, process_events
from joypad.ui.loop.frame import draw_frame, update_scroll
from joypad.ui.loop.joysticks import maybe_rescan_joysticks, rescan_joysticks
from joypad.ui.loop.poll import poll_continuous_input
from joypad.ui.loop.xinput_poll import launcher_uses_xinput, poll_xinput_input

__all__ = [
    "LoopContext",
    "RESCAN_INTERVAL",
    "draw_frame",
    "get_events",
    "handle_remap_session",
    "launcher_uses_xinput",
    "maybe_rescan_joysticks",
    "poll_continuous_input",
    "poll_xinput_input",
    "process_events",
    "rescan_joysticks",
    "update_scroll",
]
