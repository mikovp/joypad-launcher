"""Remap worker CLI entry point."""

import sys

from joypad.input.engine import run_remap_loop


def run_remap_worker_main(argv=None):
    import argparse

    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "--input-remap-worker":
        argv = argv[1:]
    parser = argparse.ArgumentParser(description="Joypad Launcher input remap worker")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--log-dir", default=".")
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--watch-exe", default="")
    parser.add_argument("--watch-dir", default="")
    parser.add_argument("--parent-pid", type=int, default=0)
    args = parser.parse_args(argv)
    run_remap_loop(
        args.profile,
        args.pid,
        user_index=args.index,
        log_dir=args.log_dir,
        log_enabled=args.log,
        watch_exe=args.watch_exe or None,
        watch_dir=args.watch_dir or None,
        parent_pid=args.parent_pid or None,
    )
