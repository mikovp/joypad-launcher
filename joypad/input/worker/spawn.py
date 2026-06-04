"""Start and stop remap worker subprocess."""

import os
import subprocess
import sys

from joypad.input.log import init_remap_log, remap_log


def start_remap_worker(profile_path, root_pid, base_dir, user_index=0, watch_exe=None, watch_dir=None, parent_pid=None, log_enabled=False):
    """Start remapping subprocess; returns Popen or None."""
    if sys.platform != "win32" or not profile_path or not root_pid:
        if log_enabled:
            init_remap_log(base_dir or ".", enabled=True)
            remap_log("start_remap_worker skipped platform=%s profile=%s pid=%s" % (sys.platform, profile_path, root_pid))
        return None
    log_dir = os.path.abspath(base_dir or ".")
    launcher_pid = int(parent_pid or os.getpid())
    worker_args = [
        "--input-remap-worker",
        "--profile",
        os.path.abspath(profile_path),
        "--pid",
        str(int(root_pid)),
        "--index",
        str(int(user_index)),
        "--log-dir",
        log_dir,
        "--parent-pid",
        str(launcher_pid),
    ]
    if watch_exe:
        worker_args.extend(["--watch-exe", watch_exe])
    if watch_dir:
        worker_args.extend(["--watch-dir", os.path.abspath(watch_dir)])
    if log_enabled:
        worker_args.append("--log")
    if getattr(sys, "frozen", False):
        cmd = [sys.executable] + worker_args
    else:
        cmd = [sys.executable, os.path.join(base_dir, "launcher.py")] + worker_args
    try:
        if log_enabled:
            init_remap_log(log_dir, enabled=True)
        proc = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        remap_log("launcher spawned worker pid=%s game_pid=%s profile=%s" % (proc.pid, root_pid, profile_path))
        remap_log("cmd: %s" % " ".join('"%s"' % c if " " in c else c for c in cmd))
        return proc
    except Exception as exc:
        if log_enabled:
            init_remap_log(log_dir, enabled=True)
            remap_log("ERROR spawn worker: %s" % exc)
        return None


def stop_remap_worker(proc, timeout=2.0):
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=timeout)
    except Exception:
        pass
    if proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=max(3.0, timeout + 1.0),
                check=False,
            )
        else:
            proc.kill()
            proc.wait(timeout=timeout)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
