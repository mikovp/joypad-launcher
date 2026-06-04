import math
import os
import sys
import time

from joypad.input.constants import (
    BTN_A, BTN_B, BTN_X, BTN_Y, BTN_LB, BTN_RB, BTN_BACK, BTN_START,
    BTN_FACE, STICK_MODES, RIGHT_STICK_MODES, TRIGGER_THRESHOLD,
    XINPUT_DPAD, XINPUT_FACE, GAME_WATCH_GRACE, GAME_WATCH_ACTIVITY_GRACE,
)
from joypad.input.bindings import VK
from joypad.input.log import remap_log, init_remap_log, remap_log_enabled
from joypad.input.profiles import (
    load_profile, prepare_profile, resolve_profile_path,
    game_remap_key, parse_slot_binding, ensure_chords,
)

# Stick click (L3 / R3)
XINPUT_L3 = 0x0040
XINPUT_R3 = 0x0080


# --- Windows input ---

if sys.platform == "win32":
    from ctypes import Structure, Union, WINFUNCTYPE, byref, c_int, c_int16, c_long, c_short, c_ubyte, c_ulong, c_ulonglong, c_void_p, c_wchar, sizeof, windll
    from ctypes.wintypes import DWORD, HANDLE, WORD

    ULONG_PTR = c_ulonglong if sizeof(c_void_p) == 8 else c_ulong

    class MOUSEINPUT(Structure):
        _fields_ = [
            ("dx", c_int),
            ("dy", c_int),
            ("mouseData", DWORD),
            ("dwFlags", DWORD),
            ("time", DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(Structure):
        _fields_ = [
            ("wVk", WORD),
            ("wScan", WORD),
            ("dwFlags", DWORD),
            ("time", DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(Structure):
        _fields_ = [("uMsg", DWORD), ("wParamL", WORD), ("wParamH", WORD)]

    class INPUT_UNION(Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(Structure):
        _fields_ = [("type", DWORD), ("u", INPUT_UNION)]

    INPUT_MOUSE = 0
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    KEYEVENTF_EXTENDEDKEY = 0x0001
    MAPVK_VK_TO_VSC = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    WHEEL_DELTA = 120

    class POINT(Structure):
        _fields_ = [("x", c_long), ("y", c_long)]

    _send_input_errors = 0

    # VKs that need KEYEVENTF_EXTENDEDKEY when sent as scan codes (DirectInput-style).
    _EXTENDED_VKS = frozenset(
        {
            0x21,
            0x22,
            0x23,
            0x24,
            0x25,
            0x26,
            0x27,
            0x28,
            0x2D,
            0x2E,
            0x5B,
            0x5C,
            0x6F,
            0x90,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
        }
    )

    def _key_event_vk(vk, down):
        flags = 0 if down else KEYEVENTF_KEYUP
        inp = INPUT(
            type=INPUT_KEYBOARD,
            u=INPUT_UNION(ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)),
        )
        _send_input(inp)

    def _key_event_scancode(vk, down):
        scan = windll.user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC) & 0xFF
        if not scan:
            _key_event_vk(vk, down)
            return
        flags = KEYEVENTF_SCANCODE
        if not down:
            flags |= KEYEVENTF_KEYUP
        if vk in _EXTENDED_VKS:
            flags |= KEYEVENTF_EXTENDEDKEY
        inp = INPUT(
            type=INPUT_KEYBOARD,
            u=INPUT_UNION(
                ki=KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
            ),
        )
        _send_input(inp)

    def _key_event(vk, down, method="scancode"):
        method = (method or "scancode").lower()
        if method == "vk":
            _key_event_vk(vk, down)
        elif method == "both":
            _key_event_scancode(vk, down)
            _key_event_vk(vk, down)
        else:
            _key_event_scancode(vk, down)

    class XINPUT_GAMEPAD(Structure):
        _fields_ = [
            ("wButtons", WORD),
            ("bLeftTrigger", c_ubyte),
            ("bRightTrigger", c_ubyte),
            ("sThumbLX", c_short),
            ("sThumbLY", c_short),
            ("sThumbRX", c_short),
            ("sThumbRY", c_short),
        ]

    class XINPUT_STATE(Structure):
        _fields_ = [("dwPacketNumber", DWORD), ("Gamepad", XINPUT_GAMEPAD)]

    _xinput = None
    for _dll in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            _xinput = windll.LoadLibrary(_dll)
            break
        except OSError:
            pass

    def _send_input(*inputs):
        global _send_input_errors
        arr = (INPUT * len(inputs))(*inputs)
        sent = windll.user32.SendInput(len(inputs), arr, sizeof(INPUT))
        if sent != len(inputs):
            _send_input_errors += 1
            if _send_input_errors <= 5:
                remap_log("SendInput sent %s/%s (err=%s)" % (sent, len(inputs), windll.kernel32.GetLastError()))
        return sent

    def _mouse_button(btn, down):
        flag_map = {
            "mouse_left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
            "mouse_right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
            "mouse_middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        }
        pair = flag_map.get(btn)
        if not pair:
            return
        inp = INPUT(type=INPUT_MOUSE, u=INPUT_UNION(mi=MOUSEINPUT(0, 0, 0, pair[0 if down else 1], 0, 0)))
        _send_input(inp)

    def _mouse_move_sendinput(dx, dy):
        inp = INPUT(type=INPUT_MOUSE, u=INPUT_UNION(mi=MOUSEINPUT(int(dx), int(dy), 0, MOUSEEVENTF_MOVE, 0, 0)))
        return _send_input(inp)

    def _mouse_move_cursor(dx, dy):
        pt = POINT()
        if not windll.user32.GetCursorPos(byref(pt)):
            return 0
        return 1 if windll.user32.SetCursorPos(pt.x + int(dx), pt.y + int(dy)) else 0

    def _mouse_move(dx, dy, method="both"):
        if dx == 0 and dy == 0:
            return
        method = (method or "both").lower()
        if method in ("sendinput", "both"):
            _mouse_move_sendinput(dx, dy)
        if method in ("cursor", "both"):
            _mouse_move_cursor(dx, dy)

    def _mouse_wheel(direction):
        delta = WHEEL_DELTA if direction == "up" else -WHEEL_DELTA
        inp = INPUT(
            type=INPUT_MOUSE,
            u=INPUT_UNION(
                mi=MOUSEINPUT(0, 0, DWORD(delta & 0xFFFFFFFF), MOUSEEVENTF_WHEEL, 0, 0)
            ),
        )
        _send_input(inp)

    def _mouse_center_screen():
        w = windll.user32.GetSystemMetrics(0)
        h = windll.user32.GetSystemMetrics(1)
        windll.user32.SetCursorPos(w // 2, h // 2)

    def _read_xinput(user_index=0):
        if not _xinput:
            return None
        state = XINPUT_STATE()
        if _xinput.XInputGetState(user_index, byref(state)) != 0:
            return None
        return state.Gamepad

    def _norm_axis(v):
        return max(-1.0, min(1.0, v / 32768.0))

    def _apply_deadzone(v, deadzone):
        if abs(v) < deadzone:
            return 0.0
        sign = 1.0 if v > 0 else -1.0
        return sign * (abs(v) - deadzone) / (1.0 - deadzone)

    def _get_process_tree_pids(root_pid):
        if not root_pid:
            return set()
        try:
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
                    ("szExeFile", c_ubyte * 260),
                ]

            kernel32 = windll.kernel32
            snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if snap in (None, INVALID_HANDLE_VALUE):
                return {int(root_pid)}
            parent_to_children = {}
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

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def _any_pid_alive(pids):
        STILL_ACTIVE = 259
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

    class RemapEngine:
        """Applies one profile to XInput state via SendInput."""

        def __init__(self, profile):
            self.profile = profile
            self.deadzone = float(profile["deadzone"])
            self.mouse_sens = float(profile["mouse_sensitivity"])
            self.mouse_scale = float(profile["mouse_scale"])
            self.mouse_accel = float(profile.get("mouse_acceleration", 0.0))
            self.mouse_accel_off_lt = bool(profile.get("mouse_accel_off_lt", False))
            self.mouse_method = str(profile["mouse_method"]).lower()
            self.keyboard_method = str(profile["keyboard_method"]).lower()
            self.button_holds = profile.get("button_holds") or {}
            self._hold_state = {}
            self._key_refcount = {}
            self._mouse_refcount = {}
            self._active_face_binding = {}
            self._prev_digital = {}
            self._prev_digital_binding = {}
            self._level_keys = {}
            self._toggle_state = {}
            self._mouse_acc_x = 0.0
            self._mouse_acc_y = 0.0
            self._mouse_sent = 0
            self._last_rx = 0.0
            self._last_ry = 0.0

        def _apply_digital(self, slot_id, binding, pressed):
            """Hold bindings + one-shot mouse wheel on rising edge."""
            was = self._prev_digital.get(slot_id, False)
            if binding in ("mouse_wheel_up", "mouse_wheel_down"):
                if pressed and not was:
                    _mouse_wheel("up" if binding == "mouse_wheel_up" else "down")
                self._prev_digital[slot_id] = pressed
                return
            if binding and binding != "none" and pressed != was:
                self._apply_binding(binding, pressed)
            elif not pressed and was:
                # Release previous binding even if caller passes "none" as binding.
                prev_binding = self._prev_digital_binding.get(slot_id)
                if prev_binding and prev_binding != "none":
                    self._apply_binding(prev_binding, False)
            if pressed and binding and binding != "none":
                self._prev_digital_binding[slot_id] = binding
            elif not pressed:
                self._prev_digital_binding.pop(slot_id, None)
            self._prev_digital[slot_id] = pressed

        def _apply_toggle(self, slot_id, binding, pressed):
            """Toggle binding on each press (rising edge); stays latched until next press."""
            was = self._prev_digital.get(slot_id, False)
            if pressed and not was:
                active = not self._toggle_state.get(slot_id, False)
                self._toggle_state[slot_id] = active
                self._apply_binding(binding, active)
            self._prev_digital[slot_id] = pressed

        def _apply_slot_binding(self, slot_id, value, pressed):
            binding, mode = parse_slot_binding(value)
            if mode == "toggle":
                self._apply_toggle(slot_id, binding, pressed)
            else:
                self._apply_digital(slot_id, binding, pressed)

        def _set_key_level(self, vk, down):
            """Level-triggered key (sticks): one press/release edge per state change."""
            was = self._level_keys.get(vk, False)
            if down == was:
                return
            self._level_keys[vk] = down
            self._set_key(vk, down)

        def _set_key(self, vk, down):
            if down:
                count = self._key_refcount.get(vk, 0) + 1
                self._key_refcount[vk] = count
                if count == 1:
                    _key_event(vk, True, self.keyboard_method)
            else:
                count = self._key_refcount.get(vk, 0)
                if count <= 0:
                    return
                count -= 1
                self._key_refcount[vk] = count
                if count == 0:
                    _key_event(vk, False, self.keyboard_method)

        def _set_mouse_btn(self, btn, down):
            if btn not in ("mouse_left", "mouse_right", "mouse_middle"):
                return
            if down:
                count = self._mouse_refcount.get(btn, 0) + 1
                self._mouse_refcount[btn] = count
                if count == 1:
                    _mouse_button(btn, True)
            else:
                count = self._mouse_refcount.get(btn, 0)
                if count <= 0:
                    return
                count -= 1
                self._mouse_refcount[btn] = count
                if count == 0:
                    _mouse_button(btn, False)

        def _apply_binding(self, binding, down):
            if not binding or binding == "none":
                return
            if binding in VK:
                self._set_key(VK[binding], down)
            elif binding.startswith("mouse_"):
                self._set_mouse_btn(binding, down)

        def _apply_with_hold(self, slot_id, tap_binding, pressed, hold_cfg):
            hold_binding = hold_cfg.get("hold", "none")
            hold_ms = max(100, int(hold_cfg.get("hold_ms", 400)))
            state = self._hold_state.setdefault(slot_id, {"start": None, "mode": None})

            if pressed:
                if state["start"] is None:
                    state["start"] = time.perf_counter()
                    state["mode"] = "waiting"
                elapsed_ms = (time.perf_counter() - state["start"]) * 1000.0
                if state["mode"] == "waiting" and elapsed_ms >= hold_ms and hold_binding != "none":
                    state["mode"] = "hold"
                    self._apply_digital(slot_id + "_hold", hold_binding, True)
                elif state["mode"] == "hold":
                    self._apply_digital(slot_id + "_hold", hold_binding, True)
            else:
                if state["mode"] == "waiting":
                    # Short tap: one-shot pulse, no key held during the wait.
                    if hold_cfg.get("center_cursor"):
                        _mouse_center_screen()
                    self._apply_digital(slot_id + "_tap", tap_binding, True)
                    self._apply_digital(slot_id + "_tap", tap_binding, False)
                elif state["mode"] == "hold":
                    self._apply_digital(slot_id + "_hold", hold_binding, False)
                state["start"] = None
                state["mode"] = None

        def _apply_stick_keys(self, mode, lx, ly):
            if mode == "wasd":
                self._set_key_level(VK["w"], ly > self.deadzone)
                self._set_key_level(VK["s"], ly < -self.deadzone)
                self._set_key_level(VK["a"], lx < -self.deadzone)
                self._set_key_level(VK["d"], lx > self.deadzone)
            elif mode == "arrows":
                self._set_key_level(0x26, ly > self.deadzone)
                self._set_key_level(0x28, ly < -self.deadzone)
                self._set_key_level(0x25, lx < -self.deadzone)
                self._set_key_level(0x27, lx > self.deadzone)

        def _resolve_face_bindings(self, pad):
            """Face buttons with LB/RB chord layers (Steam Input style)."""
            buttons = self.profile.get("buttons") or {}
            chords = ensure_chords(self.profile)
            lb_held = bool(pad.wButtons & XINPUT_FACE[BTN_LB])
            rb_held = bool(pad.wButtons & XINPUT_FACE[BTN_RB])
            lb_chord_active = False
            rb_chord_active = False
            resolved = {}

            for btn_idx in BTN_FACE:
                face_key = str(btn_idx)
                pressed = bool(pad.wButtons & XINPUT_FACE[btn_idx])
                if not pressed:
                    resolved[btn_idx] = (buttons.get(face_key, "none"), False)
                    continue

                binding = None
                if lb_held:
                    chord = (chords.get("lb") or {}).get(face_key, "none")
                    if chord and chord != "none":
                        binding = chord
                        lb_chord_active = True
                if binding is None and rb_held:
                    chord = (chords.get("rb") or {}).get(face_key, "none")
                    if chord and chord != "none":
                        binding = chord
                        rb_chord_active = True
                if binding is None:
                    binding = buttons.get(face_key, "none")
                resolved[btn_idx] = (binding, True)

            return resolved, lb_chord_active, rb_chord_active

        def _mouse_accel_multiplier(self, rx, ry, lt_pressed):
            """Boost gain at larger stick deflection; optional linear mode when LT held."""
            if self.mouse_accel <= 0:
                return 1.0
            if self.mouse_accel_off_lt and lt_pressed:
                return 1.0
            mag = min(1.0, math.hypot(rx, ry))
            return 1.0 + self.mouse_accel * (mag * mag)

        def tick(self, pad):
            if pad is None:
                self.release_all()
                return
            lx = _apply_deadzone(_norm_axis(pad.sThumbLX), self.deadzone)
            ly = _apply_deadzone(_norm_axis(pad.sThumbLY), self.deadzone)
            rx = _apply_deadzone(_norm_axis(pad.sThumbRX), self.deadzone)
            ry = _apply_deadzone(_norm_axis(pad.sThumbRY), self.deadzone)

            left_mode = self.profile.get("left_stick") or "none"
            if left_mode in STICK_MODES and left_mode != "none":
                self._apply_stick_keys(left_mode, lx, ly)
            else:
                for vk in (VK["w"], VK["a"], VK["s"], VK["d"], 0x25, 0x26, 0x27, 0x28):
                    self._set_key_level(vk, False)

            right_mode = self.profile.get("right_stick") or "none"
            self._last_rx = rx
            self._last_ry = ry
            lt_pressed = pad.bLeftTrigger >= TRIGGER_THRESHOLD
            if right_mode == "mouse":
                gain = self.mouse_sens * self.mouse_scale
                accel_mult = self._mouse_accel_multiplier(rx, ry, lt_pressed)
                self._mouse_acc_x += rx * gain * accel_mult
                self._mouse_acc_y += -ry * gain * accel_mult
                dx = int(round(self._mouse_acc_x))
                dy = int(round(self._mouse_acc_y))
                if dx:
                    self._mouse_acc_x -= dx
                if dy:
                    self._mouse_acc_y -= dy
                if dx or dy:
                    _mouse_move(dx, dy, self.mouse_method)
                    self._mouse_sent += abs(dx) + abs(dy)

            buttons = self.profile.get("buttons") or {}
            face_bindings, lb_chord_active, rb_chord_active = self._resolve_face_bindings(pad)
            for btn_idx, (binding, pressed) in face_bindings.items():
                slot_id = "btn_%s" % btn_idx
                btn_key = str(btn_idx)
                tap_binding = buttons.get(btn_key, "none")
                hold_cfg = self.button_holds.get(btn_key)

                if pressed:
                    self._active_face_binding[btn_idx] = binding
                else:
                    binding = self._active_face_binding.pop(btn_idx, tap_binding)

                if hold_cfg and tap_binding != "none" and binding == tap_binding:
                    self._apply_with_hold(slot_id, tap_binding, pressed, hold_cfg)
                else:
                    self._apply_digital(slot_id, binding, pressed)

            for btn_idx, mask in XINPUT_FACE.items():
                if btn_idx in BTN_FACE:
                    continue
                if btn_idx == BTN_LB and lb_chord_active:
                    self._apply_digital("btn_%s" % btn_idx, buttons.get(str(BTN_LB), "none"), False)
                    continue
                if btn_idx == BTN_RB and rb_chord_active:
                    self._apply_digital("btn_%s" % btn_idx, buttons.get(str(BTN_RB), "none"), False)
                    continue
                binding = buttons.get(str(btn_idx), "none")
                pressed = bool(pad.wButtons & mask)
                self._apply_digital("btn_%s" % btn_idx, binding, pressed)

            dpad_map = self.profile.get("dpad") or {}
            for dkey, mask in XINPUT_DPAD.items():
                binding = dpad_map.get(dkey, "none")
                pressed = bool(pad.wButtons & mask)
                self._apply_digital("dpad_%s" % dkey, binding, pressed)

            stick_clicks = self.profile.get("stick_clicks") or {}
            l3 = stick_clicks.get("left", "none")
            r3 = stick_clicks.get("right", "none")
            self._apply_slot_binding("stick_click_left", l3, bool(pad.wButtons & XINPUT_L3))
            self._apply_slot_binding("stick_click_right", r3, bool(pad.wButtons & XINPUT_R3))

            triggers = self.profile.get("triggers") or {}
            lt = triggers.get("left", "none")
            rt = triggers.get("right", "none")
            self._apply_digital("trigger_left", lt, pad.bLeftTrigger >= TRIGGER_THRESHOLD)
            self._apply_digital("trigger_right", rt, pad.bRightTrigger >= TRIGGER_THRESHOLD)

        def release_all(self):
            for vk, count in list(self._key_refcount.items()):
                if count > 0:
                    _key_event(vk, False, self.keyboard_method)
            self._key_refcount.clear()
            for btn, count in list(self._mouse_refcount.items()):
                if count > 0:
                    _mouse_button(btn, False)
            self._mouse_refcount.clear()
            self._prev_digital.clear()
            self._prev_digital_binding.clear()
            self._level_keys.clear()
            self._hold_state.clear()
            self._toggle_state.clear()
            self._active_face_binding.clear()

    def _enum_process_ids():
        ids = set()
        try:
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
                    ("szExeFile", c_ubyte * 260),
                ]

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

    def _process_image_path(pid):
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

    def _find_pids_in_directory(game_dir, exe_hint=None):
        game_dir = os.path.normcase(os.path.abspath(game_dir or ""))
        found = set()
        if exe_hint:
            found |= _find_pids_by_exe_name(exe_hint)
        if not game_dir or not os.path.isdir(game_dir):
            return found
        prefix = game_dir + os.sep
        try:
            for pid in _enum_process_ids():
                path = _process_image_path(pid)
                if path and path.startswith(prefix):
                    found.add(pid)
        except Exception:
            pass
        return found

    def _find_pids_by_exe_stem(stem, exact_name=None):
        """Find processes by exe name stem (e.g. duckov matches Duckov-Win64-Shipping.exe)."""
        stem = (stem or "").lower()
        exact_name = (exact_name or "").lower()
        if not stem and not exact_name:
            return set()
        try:
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
                    ("szExeFile", c_ubyte * 260),
                ]

            kernel32 = windll.kernel32
            snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if snap in (None, INVALID_HANDLE_VALUE):
                return set()
            found = set()
            try:
                pe = PROCESSENTRY32()
                pe.dwSize = sizeof(PROCESSENTRY32)
                if kernel32.Process32First(snap, byref(pe)):
                    while True:
                        name = bytes(pe.szExeFile).split(b"\0", 1)[0].decode("latin-1", "ignore").lower()
                        if exact_name and name == exact_name:
                            found.add(pe.th32ProcessID)
                        elif len(stem) >= 4 and stem in name:
                            found.add(pe.th32ProcessID)
                        if not kernel32.Process32Next(snap, byref(pe)):
                            break
            finally:
                kernel32.CloseHandle(snap)
            return found
        except Exception:
            return set()

    def _find_pids_by_exe_name(exe_name):
        exe_name = (exe_name or "").lower()
        if not exe_name:
            return set()
        stem = os.path.splitext(exe_name)[0]
        return _find_pids_by_exe_stem(stem, exe_name)

    def _find_pids_by_window_substring(text):
        """Fallback: match visible window titles (Unity/Epic games may use different exe names)."""
        needle = (text or "").lower()
        if len(needle) < 4:
            return set()
        found = set()

        def _callback(hwnd, _):
            if not windll.user32.IsWindowVisible(hwnd):
                return True
            length = windll.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = (c_wchar * (length + 1))()
            windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = (buf.value or "").lower()
            if needle in title:
                pid = DWORD()
                windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
                if pid.value:
                    found.add(int(pid.value))
            return True

        WNDENUMPROC = WINFUNCTYPE(c_int, c_void_p, c_void_p)
        try:
            windll.user32.EnumWindows(WNDENUMPROC(_callback), 0)
        except Exception:
            pass
        return found

    def _gamepad_active(pad, threshold=8000):
        if pad is None:
            return False
        if pad.wButtons:
            return True
        if pad.bLeftTrigger >= TRIGGER_THRESHOLD or pad.bRightTrigger >= TRIGGER_THRESHOLD:
            return True
        for axis in (pad.sThumbLX, pad.sThumbLY, pad.sThumbRX, pad.sThumbRY):
            if abs(int(axis)) > threshold:
                return True
        return False

    def _active_game_pids(root_pid, watch_exe=None, watch_dir=None, cached_dir_pids=None):
        pids = set()
        if root_pid:
            pids |= _get_process_tree_pids(root_pid)
        if watch_exe:
            pids |= _find_pids_by_exe_name(watch_exe)
            stem = os.path.splitext(watch_exe)[0]
            if len(stem) >= 4:
                pids |= _find_pids_by_window_substring(stem)
        if watch_dir:
            if cached_dir_pids is not None:
                pids |= cached_dir_pids
            else:
                pids |= _find_pids_in_directory(watch_dir, watch_exe)
        return pids

    def _alive_pids(pids):
        alive = set()
        access = PROCESS_QUERY_LIMITED_INFORMATION
        STILL_ACTIVE = 259
        ERROR_ACCESS_DENIED = 5
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

    def game_process_alive(root_pid, watch_exe=None, watch_dir=None, cached_dir_pids=None):
        pids = _active_game_pids(root_pid, watch_exe, watch_dir, cached_dir_pids)
        return bool(_alive_pids(pids))

    def wait_for_game_exe_exit(watch_exe, root_pid=None, watch_dir=None, grace=GAME_WATCH_GRACE, pump=None):
        """Wait until no matching game process runs (survives Epic launcher restart)."""
        if not watch_exe and not watch_dir:
            return
        last_seen = time.time()
        last_activity = last_seen
        restart_logged = False
        cached_dir_pids = set()
        last_dir_scan = 0.0
        label = watch_exe or os.path.basename(watch_dir or "game")
        while True:
            now = time.time()
            if watch_dir and now - last_dir_scan >= 1.0:
                cached_dir_pids = _find_pids_in_directory(watch_dir, watch_exe)
                last_dir_scan = now
            alive = _alive_pids(
                _active_game_pids(root_pid, watch_exe, watch_dir, cached_dir_pids)
            )
            if alive:
                last_seen = now
                last_activity = now
                if (
                    not restart_logged
                    and root_pid
                    and not _any_pid_alive({int(root_pid)})
                ):
                    remap_log("launcher wait: %s restarted (pids %s)" % (label, sorted(alive)[:4]))
                    restart_logged = True
            elif now - last_activity <= GAME_WATCH_ACTIVITY_GRACE:
                last_seen = now
            elif now - last_seen >= grace:
                remap_log("launcher wait: %s gone for %.0fs" % (label, grace))
                break
            if pump:
                pump()
            time.sleep(0.1 if pump else 0.5)

    def _scan_xinput_indices():
        found = []
        if not _xinput:
            return found
        for i in range(4):
            state = XINPUT_STATE()
            if _xinput.XInputGetState(i, byref(state)) == 0:
                gp = state.Gamepad
                found.append((i, gp.wButtons, gp.sThumbLX, gp.sThumbLY))
        return found

    def _pick_xinput_index(preferred=0):
        connected = _scan_xinput_indices()
        if not connected:
            return preferred
        indices = [c[0] for c in connected]
        if preferred in indices:
            return preferred
        remap_log("auto-selected XInput index %s (preferred %s unavailable)" % (indices[0], preferred))
        return indices[0]

    def run_remap_loop(
        profile_path,
        root_pid,
        user_index=0,
        poll_ms=8,
        log_dir=None,
        log_enabled=False,
        watch_exe=None,
        watch_dir=None,
        parent_pid=None,
    ):
        if log_enabled and log_dir:
            init_remap_log(log_dir)
        remap_log(
            "worker start profile=%s watch_pid=%s xinput_index=%s"
            % (os.path.abspath(profile_path), root_pid, user_index)
        )
        if not _xinput:
            remap_log("ERROR: XInput DLL not found (xinput1_4 / xinput1_3 / xinput9_1_0)")
            return
        connected = _scan_xinput_indices()
        if connected:
            for idx, btns, lx, ly in connected:
                remap_log("XInput[%s] ok buttons=0x%04x stick=(%s,%s)" % (idx, btns, lx, ly))
        else:
            remap_log("WARN: no XInput controllers on indices 0-3")
        if user_index not in [c[0] for c in connected] and connected:
            remap_log(
                "WARN: configured index %s has no pad; active indices: %s"
                % (user_index, [c[0] for c in connected])
            )
        user_index = _pick_xinput_index(user_index)
        if watch_exe:
            remap_log("watch exe: %s" % watch_exe)
        if watch_dir:
            remap_log("watch dir: %s" % watch_dir)

        if parent_pid:
            remap_log("watch launcher pid: %s" % parent_pid)
        profile = load_profile(profile_path, base_dir=log_dir)
        engine = RemapEngine(profile)
        remap_log(
            "mouse method=%s sens=%s scale=%s keyboard=%s"
            % (
                engine.mouse_method,
                engine.mouse_sens,
                engine.mouse_scale,
                engine.keyboard_method,
            )
        )
        ticks = 0
        last_status = time.time()
        last_watch_check = 0.0
        last_parent_check = 0.0
        mouse_sent_prev = 0
        last_seen = time.time()
        last_activity = last_seen
        restart_logged = False
        cached_dir_pids = set()
        last_dir_scan = 0.0
        watch_label = watch_exe or os.path.basename(watch_dir or "game")
        use_watch = bool(watch_exe or watch_dir)
        try:
            while True:
                now = time.time()
                pad = _read_xinput(user_index)
                if _gamepad_active(pad):
                    last_activity = now
                if parent_pid and now - last_parent_check >= 0.5:
                    if not _any_pid_alive({int(parent_pid)}):
                        remap_log("worker exit: launcher pid %s gone" % parent_pid)
                        break
                    last_parent_check = now
                if use_watch and now - last_watch_check >= 0.5:
                    if watch_dir and now - last_dir_scan >= 1.0:
                        cached_dir_pids = _find_pids_in_directory(watch_dir, watch_exe)
                        last_dir_scan = now
                    alive = _alive_pids(
                        _active_game_pids(root_pid, watch_exe, watch_dir, cached_dir_pids)
                    )
                    if alive:
                        last_seen = now
                        last_activity = now
                        if not restart_logged and root_pid and not _any_pid_alive({int(root_pid)}):
                            remap_log(
                                "worker survived game restart (%s pids %s)"
                                % (watch_label, sorted(alive)[:4])
                            )
                            restart_logged = True
                    elif now - last_activity <= GAME_WATCH_ACTIVITY_GRACE:
                        last_seen = now
                    elif now - last_seen >= GAME_WATCH_GRACE:
                        remap_log("worker exit: %s gone for %.0fs" % (watch_label, GAME_WATCH_GRACE))
                        break
                    last_watch_check = now
                elif not use_watch and not _any_pid_alive(_get_process_tree_pids(root_pid)):
                    break

                engine.tick(pad)
                ticks += 1
                if ticks == 1:
                    remap_log("loop running pad=%s" % ("ok" if pad else "none"))
                if now - last_status >= 2.0:
                    if use_watch:
                        alive = _alive_pids(
                            _active_game_pids(root_pid, watch_exe, watch_dir, cached_dir_pids)
                        )
                        pid_count = len(alive)
                    else:
                        pid_count = len(_alive_pids(_get_process_tree_pids(root_pid)))
                    sent_delta = engine._mouse_sent - mouse_sent_prev
                    mouse_sent_prev = engine._mouse_sent
                    remap_log(
                        "alive ticks=%s alive_pids=%s pad=%s keys=%s stick=(%.2f,%.2f) mouse_px=%s"
                        % (
                            ticks,
                            pid_count,
                            "ok" if pad else "none",
                            sum(1 for c in engine._key_refcount.values() if c > 0),
                            engine._last_rx,
                            engine._last_ry,
                            sent_delta,
                        )
                    )
                    last_status = now
                time.sleep(poll_ms / 1000.0)
        except Exception as exc:
            remap_log("ERROR loop: %s" % exc)
            raise
        finally:
            remap_log("worker stop ticks=%s" % ticks)
            engine.release_all()

else:

    def run_remap_loop(profile_path, root_pid, user_index=0, poll_ms=8):
        raise RuntimeError("Input remapping is supported on Windows only")

    def wait_for_game_exe_exit(watch_exe, root_pid=None, watch_dir=None, grace=GAME_WATCH_GRACE, pump=None):
        pass

    def game_process_alive(root_pid, watch_exe=None, watch_dir=None, cached_dir_pids=None):
        return False
