"""Win32 ctypes structures for process enumeration."""

from ctypes import Structure, c_ubyte, c_ulong
from ctypes.wintypes import DWORD

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


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
        ("szExeFile", c_ubyte * 260),
    ]
