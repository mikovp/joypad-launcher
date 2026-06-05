import pygame

from joypad.input.constants import BTN_B
from joypad.platform.windows.hwnd.timed_pump import wait_cancel_pressed


def test_wait_cancel_escape(monkeypatch):
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
    )
    assert wait_cancel_pressed() is True


def test_wait_cancel_button_b(monkeypatch):
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [pygame.event.Event(pygame.JOYBUTTONDOWN, button=BTN_B)],
    )
    assert wait_cancel_pressed() is True


def test_wait_cancel_ignores_other_input(monkeypatch):
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
            pygame.event.Event(pygame.JOYBUTTONDOWN, button=0),
        ],
    )
    assert wait_cancel_pressed() is False
