# coding = utf-8
# DDC/CI via Windows API — from https://github.com/thlter/DDCCI_tool (MIT)

import ctypes
import logging
from ctypes import wintypes
from typing import Tuple

from . import vcp_code

_LOGGER = logging.getLogger(__name__)


def _get_physical_monitors_from_hmonitor(hmonitor: wintypes.HMONITOR) -> list:
    class _PhysicalMonitorStructure(ctypes.Structure):
        _fields_ = [
            ("hPhysicalMonitor", wintypes.HANDLE),
            ("szPhysicalMonitorDescription", wintypes.WCHAR * 128),
        ]

    phy_monitor_number = wintypes.DWORD()
    api_call_get_number = ctypes.windll.Dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR
    if not api_call_get_number(hmonitor, ctypes.byref(phy_monitor_number)):
        _LOGGER.error(ctypes.WinError())
        return []

    api_call_get_monitor = ctypes.windll.Dxva2.GetPhysicalMonitorsFromHMONITOR
    phy_monitor_array = (_PhysicalMonitorStructure * phy_monitor_number.value)()
    if not api_call_get_monitor(hmonitor, phy_monitor_number, phy_monitor_array):
        _LOGGER.error(ctypes.WinError())
        return []

    return list(phy_monitor_array)


def enumerate_monitors() -> list:
    all_hmonitor = []

    _MONITOR_ENUM_PROC = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(wintypes.LPRECT),
        wintypes.LPARAM,
    )

    def __monitor_enum_proc_callback(hmonitor_, hdc, lprect, lparam) -> bool:
        all_hmonitor.append(hmonitor_)
        return True

    if not ctypes.windll.user32.EnumDisplayMonitors(
        None, None, _MONITOR_ENUM_PROC(__monitor_enum_proc_callback), None
    ):
        raise ctypes.WinError()

    handles = []
    for hmonitor in all_hmonitor:
        handles.extend(_get_physical_monitors_from_hmonitor(hmonitor))

    return handles


class PhyMonitor(object):
    def __init__(self, phy_monitor):
        self._phy_monitor = phy_monitor
        self._phy_monitor_handle = self._phy_monitor.hPhysicalMonitor
        self.description = self._phy_monitor.szPhysicalMonitorDescription or ""
        self._caps_string = ''
        self.model = ''
        self.info_display_type = ''

        self._get_monitor_caps()
        if self._caps_string != '':
            self._get_model_info()

    def _get_monitor_caps(self):
        caps_string_length = wintypes.DWORD()
        if not ctypes.windll.Dxva2.GetCapabilitiesStringLength(
            self._phy_monitor_handle, ctypes.byref(caps_string_length)
        ):
            _LOGGER.error(ctypes.WinError())
            raise ctypes.WinError()

        caps_string = (ctypes.c_char * caps_string_length.value)()
        if not ctypes.windll.Dxva2.CapabilitiesRequestAndCapabilitiesReply(
            self._phy_monitor_handle, caps_string, caps_string_length
        ):
            _LOGGER.error(ctypes.WinError())
            return

        self._caps_string = caps_string.value.decode('ASCII')

    def _get_model_info(self):
        def find_(src: str, start_: str, end_: str) -> str:
            start_index = src.find(start_)
            if start_index == -1:
                return ''
            start_index = start_index + len(start_)
            end_index = src.find(end_, start_index)
            if end_index == -1:
                return ''
            return src[start_index:end_index]

        model = find_(self._caps_string, 'model(', ')')
        if model == '':
            _LOGGER.warning(
                'unable to find model info in vcp caps string: {}'.format(self._caps_string)
            )
        self.model = model

        info_display_type = find_(self._caps_string, 'type(', ')')
        if info_display_type == '':
            _LOGGER.warning(
                'unable to find display type info in vcp caps string: {}'.format(self._caps_string)
            )
        self.info_display_type = info_display_type

    def close(self):
        api_call = ctypes.windll.Dxva2.DestroyPhysicalMonitor
        if not api_call(self._phy_monitor_handle):
            _LOGGER.error(ctypes.WinError())

    def send_vcp_code(self, code: int, value: int) -> bool:
        if code is None:
            _LOGGER.error('vcp code to send is None. ignored.')
            return False

        api_call = ctypes.windll.Dxva2.SetVCPFeature
        code = wintypes.BYTE(code)
        new_value = wintypes.DWORD(value)
        api_call.restype = ctypes.c_bool
        ret_ = api_call(self._phy_monitor_handle, code, new_value)
        if not ret_:
            vcp_hex = int(code) if isinstance(code, int) else int(code.value)
            _LOGGER.error('send vcp command failed: ' + hex(vcp_hex))
            _LOGGER.error(ctypes.WinError())
        return ret_

    def read_vcp_code(self, code: int) -> Tuple[int, int]:
        if code is None:
            _LOGGER.error('vcp code to send is None. ignored.')
            return 0, 0

        api_call = ctypes.windll.Dxva2.GetVCPFeatureAndVCPFeatureReply
        api_in_vcp_code = wintypes.BYTE(code)
        api_out_current_value = wintypes.DWORD()
        api_out_max_value = wintypes.DWORD()

        if not api_call(
            self._phy_monitor_handle,
            api_in_vcp_code,
            None,
            ctypes.byref(api_out_current_value),
            ctypes.byref(api_out_max_value),
        ):
            _LOGGER.error('get vcp command failed: ' + hex(code))
            _LOGGER.error(ctypes.WinError())
        return api_out_current_value.value, api_out_max_value.value

    def set_vcp_value_by_name(self, vcp_code_key: str, value: int) -> bool:
        return self.send_vcp_code(vcp_code.VCP_CODE.get(vcp_code_key), value)

    def get_vcp_value_by_name(self, vcp_code_key: str) -> Tuple[int, int]:
        return self.read_vcp_code(vcp_code.VCP_CODE.get(vcp_code_key))

    @property
    def power_mode_list(self) -> list:
        return list(vcp_code.POWER_MODE_CODE.keys())

    @property
    def power_mode(self):
        power_ = self.get_vcp_value_by_name('Power Mode')[0]
        for i in list(vcp_code.POWER_MODE_CODE.keys()):
            if vcp_code.POWER_MODE_CODE[i] == power_:
                return i
        return 'off'

    @power_mode.setter
    def power_mode(self, mode: str):
        if mode not in self.power_mode_list:
            _LOGGER.warning('invalid power mode: {}, available:{}'.format(
                mode, self.power_mode_list))
            return
        self.set_vcp_value_by_name('Power Mode', vcp_code.POWER_MODE_CODE.get(mode))

    def supports_power_off(self):
        caps = (self._caps_string or "").lower()
        if "d6(" in caps:
            return True
        _cur, max_val = self.get_vcp_value_by_name('Power Mode')
        return max_val > 0

    def power_off(self):
        """Turn monitor off; tries VCP 0x05, 0x04, 0x01+off variants from caps."""
        candidates = [
            vcp_code.POWER_MODE_CODE["off"],
            4,
            3,
            2,
        ]
        seen = set()
        for value in candidates:
            if value in seen:
                continue
            seen.add(value)
            if self.set_vcp_value_by_name("Power Mode", value):
                return True
        return False


def open_phy_monitors():
    """Return PhyMonitor instances for all DDC/CI-capable displays."""
    phy_monitors = []
    seen_handles = set()
    for handle in enumerate_monitors():
        handle_val = handle.hPhysicalMonitor
        if handle_val in seen_handles:
            continue
        seen_handles.add(handle_val)
        try:
            phy_monitors.append(PhyMonitor(handle))
        except OSError as err:
            _LOGGER.error(err)
    return phy_monitors
