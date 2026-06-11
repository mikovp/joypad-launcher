from joypad.input.remap_engine.digital import RemapDigital


class _HoldHarness(RemapDigital):
    def __init__(self):
        self._hold_state = {}
        self._prev_digital = {}
        self._prev_digital_binding = {}
        self._pending_cursor_center_at = None

    def _apply_binding(self, binding, pressed):
        pass

    def _set_key_level(self, *args):
        pass


def test_center_cursor_on_hold_fires_after_button_release(monkeypatch):
    centered = []
    now = [0.0]
    monkeypatch.setattr(
        "joypad.input.remap_engine.digital.time.perf_counter", lambda: now[0]
    )
    monkeypatch.setattr(
        "joypad.input.remap_engine.digital.mouse_center_screen",
        lambda: centered.append(True),
    )

    rem = _HoldHarness()
    rem._pending_cursor_center_at = None
    cfg = {
        "hold": "u",
        "hold_ms": 100,
        "center_cursor_on_hold": True,
        "center_cursor_delay_ms": 50,
    }

    rem._apply_with_hold("btn_0", "f", True, cfg)
    now[0] = 0.15
    rem._apply_with_hold("btn_0", "f", True, cfg)
    rem._apply_with_hold("btn_0", "f", False, cfg)

    assert centered == []
    now[0] = 0.21
    rem._process_pending_cursor_center()
    assert centered == [True]


def test_short_tap_does_not_schedule_center_on_hold(monkeypatch):
    centered = []
    now = [0.0]
    monkeypatch.setattr(
        "joypad.input.remap_engine.digital.time.perf_counter", lambda: now[0]
    )
    monkeypatch.setattr(
        "joypad.input.remap_engine.digital.mouse_center_screen",
        lambda: centered.append(True),
    )

    rem = _HoldHarness()
    rem._pending_cursor_center_at = None
    cfg = {
        "hold": "u",
        "hold_ms": 100,
        "center_cursor_on_hold": True,
        "center_cursor_delay_ms": 50,
    }

    rem._apply_with_hold("btn_0", "f", True, cfg)
    now[0] = 0.05
    rem._apply_with_hold("btn_0", "f", False, cfg)
    now[0] = 1.0
    rem._process_pending_cursor_center()

    assert centered == []
    assert rem._pending_cursor_center_at is None
