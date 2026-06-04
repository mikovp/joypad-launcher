"""Key and mouse output with refcount tracking."""

from joypad.input.bindings import VK
from joypad.input.sendinput import key_event, mouse_button


class RemapOutput:
    def _set_key_level(self, vk, down):
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
                key_event(vk, True, self.keyboard_method)
        else:
            count = self._key_refcount.get(vk, 0)
            if count <= 0:
                return
            count -= 1
            self._key_refcount[vk] = count
            if count == 0:
                key_event(vk, False, self.keyboard_method)

    def _set_mouse_btn(self, btn, down):
        if btn not in ("mouse_left", "mouse_right", "mouse_middle"):
            return
        if down:
            count = self._mouse_refcount.get(btn, 0) + 1
            self._mouse_refcount[btn] = count
            if count == 1:
                mouse_button(btn, True)
        else:
            count = self._mouse_refcount.get(btn, 0)
            if count <= 0:
                return
            count -= 1
            self._mouse_refcount[btn] = count
            if count == 0:
                mouse_button(btn, False)

    def _apply_binding(self, binding, down):
        if not binding or binding == "none":
            return
        if binding in VK:
            self._set_key(VK[binding], down)
        elif binding.startswith("mouse_"):
            self._set_mouse_btn(binding, down)
