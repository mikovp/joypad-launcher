"""Non-Windows remap loop stub."""


def run_remap_loop(profile_path, root_pid, user_index=0, poll_ms=8, **kwargs):
    raise RuntimeError("Input remapping is supported on Windows only")
