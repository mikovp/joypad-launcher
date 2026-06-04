"""Backward-compatible re-export; prefer ``joypad.ui.loop``."""

from joypad.ui.loop import (
    RESCAN_INTERVAL,
    LoopContext,
    draw_frame,
    get_events,
    handle_remap_session,
    maybe_rescan_joysticks,
    poll_continuous_input,
    process_events,
    rescan_joysticks,
    update_scroll,
)

__all__ = [
    "LoopContext",
    "RESCAN_INTERVAL",
    "draw_frame",
    "get_events",
    "handle_remap_session",
    "maybe_rescan_joysticks",
    "poll_continuous_input",
    "process_events",
    "rescan_joysticks",
    "update_scroll",
]
