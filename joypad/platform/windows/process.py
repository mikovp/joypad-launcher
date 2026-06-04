"""Windows process tree enumeration."""

import sys


def get_process_and_descendant_pids(pid):
    """Returns [pid] + all child PIDs recursively (Windows, Toolhelp32)."""
    if not pid or sys.platform != "win32":
        return [pid] if pid else []
    try:
        from ctypes import Structure, byref, c_char, c_ulong, sizeof, windll
        from ctypes.wintypes import DWORD
        kernel32 = windll.kernel32
        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = 0xFFFFFFFF

        class PROCESSENTRY32(Structure):
            _fields_ = [
                ("dwSize", DWORD),
                ("cntUsage", DWORD),
                ("th32ProcessID", DWORD),
                ("th32DefaultHeapID", c_ulong),
                ("th32ModuleID", DWORD),
                ("cntThreads", DWORD),
                ("th32ParentProcessID", DWORD),
                ("pcPriClassBase", c_ulong),
                ("dwFlags", DWORD),
                ("szExeFile", c_char * 260),
            ]
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == INVALID_HANDLE_VALUE or snap is None:
            return [pid]
        parent_to_children = {}
        try:
            pe = PROCESSENTRY32()
            pe.dwSize = sizeof(PROCESSENTRY32)
            if not kernel32.Process32First(snap, byref(pe)):
                return [pid]
            while True:
                parent_to_children.setdefault(pe.th32ParentProcessID, []).append(pe.th32ProcessID)
                if not kernel32.Process32Next(snap, byref(pe)):
                    break
        finally:
            kernel32.CloseHandle(snap)
        result = [pid]
        to_visit = [pid]
        while to_visit:
            p = to_visit.pop()
            for child in parent_to_children.get(p, []):
                if child not in result:
                    result.append(child)
                    to_visit.append(child)
        return result
    except Exception:
        return [pid] if pid else []


# Backward-compatible alias used by wait.py
_get_process_and_descendant_pids = get_process_and_descendant_pids
