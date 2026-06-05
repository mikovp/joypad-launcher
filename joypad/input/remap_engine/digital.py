"""Digital, toggle, and hold slot binding application."""

import time

from joypad.input.profiles import parse_slot_binding
from joypad.input.remap_engine.output import RemapOutput
from joypad.input.sendinput import mouse_center_screen, mouse_wheel


class RemapDigital(RemapOutput):
    def _apply_digital(self, slot_id, binding, pressed):
        was = self._prev_digital.get(slot_id, False)
        if binding in ("mouse_wheel_up", "mouse_wheel_down"):
            if pressed and not was:
                mouse_wheel("up" if binding == "mouse_wheel_up" else "down")
            self._prev_digital[slot_id] = pressed
            return
        if binding and binding != "none" and pressed != was:
            self._apply_binding(binding, pressed)
        elif not pressed and was:
            prev_binding = self._prev_digital_binding.get(slot_id)
            if prev_binding and prev_binding != "none":
                self._apply_binding(prev_binding, False)
        if pressed and binding and binding != "none":
            self._prev_digital_binding[slot_id] = binding
        elif not pressed:
            self._prev_digital_binding.pop(slot_id, None)
        self._prev_digital[slot_id] = pressed

    def _apply_toggle(self, slot_id, binding, pressed):
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
            elapsed_ms = 0.0
            if state["start"] is not None:
                elapsed_ms = (time.perf_counter() - state["start"]) * 1000.0
            if state["mode"] == "waiting" and elapsed_ms < hold_ms:
                if hold_cfg.get("center_cursor"):
                    mouse_center_screen()
                self._apply_digital(slot_id + "_tap", tap_binding, True)
                self._apply_digital(slot_id + "_tap", tap_binding, False)
            elif state["mode"] == "hold":
                self._apply_digital(slot_id + "_hold", hold_binding, False)
            state["start"] = None
            state["mode"] = None
