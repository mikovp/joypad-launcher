"""Launching-game spinner overlay."""

import math
import time

import pygame

_LAUNCH_SPINNER_INTRO_FRAMES = 36
_LAUNCH_SPINNER_FRAME_DELAY = 0.1


def capture_launching_snapshot(state):
    """Frozen launcher frame for the launching spinner overlay."""
    return state.screen.copy()


def draw_launching_spinner_frame(state, saved, frame_i):
    """One spinner frame on top of the saved launcher snapshot."""
    blur_scale = 5
    dim_alpha = 140
    dot_count = 12
    r_max, r_min = 7, 1
    orbit_radius = 26
    dim_color = tuple(max(0, min(255, int(c * 0.2))) for c in state.text_color)
    small = pygame.transform.smoothscale(saved, (max(1, state.w // blur_scale), max(1, state.h // blur_scale)))
    blurred = pygame.transform.smoothscale(small, (state.w, state.h))
    state.screen.blit(blurred, (0, 0))
    dim = pygame.Surface((state.w, state.h))
    dim.set_alpha(dim_alpha)
    dim.fill((0, 0, 0))
    state.screen.blit(dim, (0, 0))
    phase = (frame_i % dot_count)
    cx, cy = state.w // 2, state.h // 2
    for j in range(dot_count):
        raw = (phase - j) % dot_count
        dist = raw if raw <= dot_count / 2 else dot_count - raw
        if raw > dot_count / 2:
            dist = 999
        t = min(1.0, dist / 6.0)
        radius = max(r_min, r_max - t * (r_max - r_min))
        t_soft = t * t
        brightness = max(0.0, 1.0 - t_soft * 1.1)
        color = tuple(
            max(0, min(255, int(dim_color[c] + (state.text_color[c] - dim_color[c]) * brightness)))
            for c in range(3)
        )
        angle = math.radians(j * (360 / dot_count) - 90)
        x = cx + orbit_radius * math.cos(angle)
        y = cy + orbit_radius * math.sin(angle)
        pygame.draw.circle(state.screen, color, (int(x), int(y)), max(1, int(radius)))


def tick_launching_spinner(state, saved, frame_i, *, sleep=False, frame_delay=_LAUNCH_SPINNER_FRAME_DELAY):
    """Advance and show one spinner frame; returns next frame index."""
    draw_launching_spinner_frame(state, saved, frame_i)
    pygame.display.flip()
    pygame.event.pump()
    if sleep:
        time.sleep(frame_delay)
    return frame_i + 1


def begin_launching_overlay(state, _game_name=None, intro_frames=_LAUNCH_SPINNER_INTRO_FRAMES):
    """Capture screen and run intro spinner; returns (snapshot, next_frame) for continued ticks."""
    saved = capture_launching_snapshot(state)
    frame = 0
    for _ in range(intro_frames):
        frame = tick_launching_spinner(state, saved, frame, sleep=True)
    return saved, frame


def show_launching_overlay(state, _game_name=None):
    """Blurred overlay with rotating dots (intro only; use tick_launching_spinner while waiting)."""
    begin_launching_overlay(state, _game_name)
