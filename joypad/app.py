#!/usr/bin/env python3
"""
Joypad Launcher application entry point.
"""

import os
import sys

try:
    import pygame
except ImportError:
    print("Install pygame: pip install pygame")
    sys.exit(1)

from joypad.bootstrap import bootstrap
from joypad.launch.session import make_on_launch, register_remap_cleanup
from joypad.paths import _BASE_DIR
from joypad.platform.windows import show_error_message
from joypad.ui import loop as inp


def run():
    boot = bootstrap()
    state = boot.state
    launch = boot.launch

    clock = pygame.time.Clock()
    loop_ctx = inp.LoopContext()
    joysticks = inp.rescan_joysticks()
    stop_active_remap = register_remap_cleanup(launch.active_remap_proc)
    on_launch = make_on_launch(state, launch, loop_ctx)

    while state.running:
        joysticks = inp.maybe_rescan_joysticks(loop_ctx, joysticks)
        events = inp.get_events()
        if inp.handle_remap_session(state, events, loop_ctx, joysticks, clock):
            continue
        joysticks, should_exit = inp.process_events(state, events, loop_ctx, joysticks, on_launch)
        if should_exit:
            break
        inp.poll_continuous_input(state, loop_ctx, joysticks)
        inp.update_scroll(state)
        inp.draw_frame(state)
        clock.tick(60)

    stop_active_remap()
    pygame.quit()


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    if len(argv) >= 2 and argv[1] == "--input-remap-worker":
        from joypad.input.worker import run_remap_worker_main

        run_remap_worker_main()
        return 0
    try:
        run()
        return 0
    except BaseException:
        import traceback

        log_path = os.path.join(_BASE_DIR, "launcher_error.log")
        err_text = traceback.format_exc()
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err_text)
        except Exception:
            pass
        traceback.print_exc()
        show_error_message("Launch error.\nDetails written to:\n%s" % log_path)
        return 1
