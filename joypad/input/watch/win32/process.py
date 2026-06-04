"""Process tree, liveness, and image path queries."""

import os
from ctypes import byref, c_wchar, sizeof, windll
from ctypes.wintypes import DWORD

from joypad.input.watch.win32.types import PROCESS_QUERY_LIMITED_INFORMATION, PROCESSENTRY32

TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = 0xFFFFFFFF
STILL_ACTIVE = 259
ERROR_ACCESS_DENIED = 5


def get_process_tree_pids(root_pid):
    if not root_pid:
        return set()
    try:
        kernel32 = windll.kernel32
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap in (None, INVALID_HANDLE_VALUE):
            return {int(root_pid)}
        parent_to_children: dict[int, list[int]] = {}
        try:
            pe = PROCESSENTRY32()
            pe.dwSize = sizeof(PROCESSENTRY32)
            if kernel32.Process32First(snap, byref(pe)):
                while True:
                    parent_to_children.setdefault(pe.th32ParentProcessID, []).append(pe.th32ProcessID)
                    if not kernel32.Process32Next(snap, byref(pe)):
                        break
        finally:
            kernel32.CloseHandle(snap)
        result = {int(root_pid)}
        stack = [int(root_pid)]
        while stack:
            p = stack.pop()
            for child in parent_to_children.get(p, []):
                if child not in result:
                    result.add(child)
                    stack.append(child)
        return result
    except Exception:
        return {int(root_pid)}


def any_pid_alive(pids):
    access = PROCESS_QUERY_LIMITED_INFORMATION
    for pid in pids:
        handle = windll.kernel32.OpenProcess(access, False, pid)
        if not handle:
            continue
        try:
            code = DWORD()
            if windll.kernel32.GetExitCodeProcess(handle, byref(code)):
                if code.value == STILL_ACTIVE:
                    return True
        finally:
            windll.kernel32.CloseHandle(handle)
    return False


def enum_process_ids():
    ids: set[int] = set()
    try:
        kernel32 = windll.kernel32
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap in (None, INVALID_HANDLE_VALUE):
            return ids
        try:
            pe = PROCESSENTRY32()
            pe.dwSize = sizeof(PROCESSENTRY32)
            if kernel32.Process32First(snap, byref(pe)):
                while True:
                    ids.add(pe.th32ProcessID)
                    if not kernel32.Process32Next(snap, byref(pe)):
                        break
        finally:
            kernel32.CloseHandle(snap)
    except Exception:
        pass
    return ids


def process_image_path(pid):
    access = PROCESS_QUERY_LIMITED_INFORMATION
    handle = windll.kernel32.OpenProcess(access, False, int(pid))
    if not handle:
        return None
    try:
        size = DWORD(32768)
        buf = (c_wchar * 32768)()
        if windll.kernel32.QueryFullProcessImageNameW(handle, 0, buf, byref(size)):
            return os.path.normcase(buf.value)
    finally:
        windll.kernel32.CloseHandle(handle)
    return None


def alive_pids(pids):
    alive = set()
    access = PROCESS_QUERY_LIMITED_INFORMATION
    for pid in pids:
        handle = windll.kernel32.OpenProcess(access, False, int(pid))
        if not handle:
            if windll.kernel32.GetLastError() == ERROR_ACCESS_DENIED:
                alive.add(int(pid))
            continue
        try:
            code = DWORD()
            if windll.kernel32.GetExitCodeProcess(handle, byref(code)):
                if code.value == STILL_ACTIVE:
                    alive.add(int(pid))
        finally:
            windll.kernel32.CloseHandle(handle)
    return alive
