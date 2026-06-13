"""RemapEngine: profile → XInput → SendInput."""

from joypad.input.constants import (
    BTN_FACE,
    BTN_LB,
    BTN_RB,
    STICK_MODES,
    TRIGGER_THRESHOLD,
    XINPUT_DPAD,
    XINPUT_FACE,
)
from joypad.input.remap_engine.digital import RemapDigital
from joypad.input.remap_face import resolve_face_bindings
from joypad.input.remap_sticks import apply_stick_keys, clear_stick_keys, mouse_accel_multiplier
from joypad.input.sendinput import key_event, mouse_button, mouse_move
from joypad.input.xinput import XINPUT_L3, XINPUT_R3, apply_deadzone, norm_axis


class RemapEngine(RemapDigital):
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
        self._pending_cursor_center_at = None

    def _any_face_pressed(self, pad):
        return any(bool(pad.wButtons & XINPUT_FACE[btn_idx]) for btn_idx in BTN_FACE)

    def _bumper_combo_active(self, pad):
        combo_binding = self.profile.get("bumper_combo") or "none"
        if combo_binding == "none":
            return False, combo_binding
        lb_pressed = bool(pad.wButtons & XINPUT_FACE[BTN_LB])
        rb_pressed = bool(pad.wButtons & XINPUT_FACE[BTN_RB])
        active = lb_pressed and rb_pressed and not self._any_face_pressed(pad)
        return active, combo_binding

    def _clear_bumper_hold_state(self, slot_id, hold_cfg):
        state = self._hold_state.get(slot_id)
        if not state:
            return
        if state.get("mode") == "hold" and hold_cfg:
            hold_binding = hold_cfg.get("hold", "none")
            if hold_binding != "none":
                self._apply_digital(slot_id + "_hold", hold_binding, False)
        state["start"] = None
        state["mode"] = None

    def tick(self, pad):
        if pad is None:
            self.release_all()
            return
        lx = apply_deadzone(norm_axis(pad.sThumbLX), self.deadzone)
        ly = apply_deadzone(norm_axis(pad.sThumbLY), self.deadzone)
        rx = apply_deadzone(norm_axis(pad.sThumbRX), self.deadzone)
        ry = apply_deadzone(norm_axis(pad.sThumbRY), self.deadzone)

        left_mode = self.profile.get("left_stick") or "none"
        if left_mode in STICK_MODES and left_mode != "none":
            apply_stick_keys(self._set_key_level, left_mode, self.deadzone, lx, ly)
        else:
            clear_stick_keys(self._set_key_level)

        right_mode = self.profile.get("right_stick") or "none"
        self._last_rx = rx
        self._last_ry = ry
        lt_pressed = pad.bLeftTrigger >= TRIGGER_THRESHOLD
        if right_mode == "mouse":
            gain = self.mouse_sens * self.mouse_scale
            accel_mult = mouse_accel_multiplier(
                self.mouse_accel, self.mouse_accel_off_lt, rx, ry, lt_pressed
            )
            self._mouse_acc_x += rx * gain * accel_mult
            self._mouse_acc_y += -ry * gain * accel_mult
            dx = int(round(self._mouse_acc_x))
            dy = int(round(self._mouse_acc_y))
            if dx:
                self._mouse_acc_x -= dx
            if dy:
                self._mouse_acc_y -= dy
            if dx or dy:
                mouse_move(dx, dy, self.mouse_method)
                self._mouse_sent += abs(dx) + abs(dy)

        buttons = self.profile.get("buttons") or {}
        face_bindings = resolve_face_bindings(self.profile, pad)
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

        combo_active, combo_binding = self._bumper_combo_active(pad)
        self._apply_digital("bumper_combo", combo_binding, combo_active)

        for btn_idx, mask in XINPUT_FACE.items():
            if btn_idx in BTN_FACE:
                continue
            slot_id = "btn_%s" % btn_idx
            btn_key = str(btn_idx)
            tap_binding = buttons.get(btn_key, "none")
            hold_cfg = self.button_holds.get(btn_key)
            pressed = bool(pad.wButtons & mask)
            if combo_active and btn_idx in (BTN_LB, BTN_RB):
                self._clear_bumper_hold_state(slot_id, hold_cfg)
                self._apply_digital(slot_id, tap_binding, False)
                continue
            if hold_cfg and tap_binding != "none":
                self._apply_with_hold(slot_id, tap_binding, pressed, hold_cfg)
            else:
                self._apply_digital(slot_id, tap_binding, pressed)

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
        self._process_pending_cursor_center()

    def release_all(self):
        for vk, count in list(self._key_refcount.items()):
            if count > 0:
                key_event(vk, False, self.keyboard_method)
        self._key_refcount.clear()
        for btn, count in list(self._mouse_refcount.items()):
            if count > 0:
                mouse_button(btn, False)
        self._mouse_refcount.clear()
        self._prev_digital.clear()
        self._prev_digital_binding.clear()
        self._level_keys.clear()
        self._hold_state.clear()
        self._toggle_state.clear()
        self._active_face_binding.clear()
        self._pending_cursor_center_at = None
