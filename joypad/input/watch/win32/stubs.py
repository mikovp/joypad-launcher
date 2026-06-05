"""Non-Windows stubs for process watch helpers."""


def wait_for_game_exe_exit(watch_exe, root_pid=None, watch_dir=None, grace=None, pump=None):
    return False


def game_process_alive(root_pid, watch_exe=None, watch_dir=None, cached_dir_pids=None):
    return False


def active_game_pids(root_pid, watch_exe=None, watch_dir=None, cached_dir_pids=None):
    return set()


def alive_pids(pids):
    return set()


def any_pid_alive(pids):
    return False


def find_pids_in_directory(game_dir, exe_hint=None):
    return set()


def get_process_tree_pids(root_pid):
    return set()
