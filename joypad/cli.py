"""Command-line flags for JoypadLauncher.exe."""

from __future__ import annotations

from dataclasses import dataclass

POWER_OFF_DISPLAY_FLAG = "--power-off-display"
POWER_OFF_ONLY_FLAG = "--power-off-only"


@dataclass(frozen=True)
class LauncherCli:
    force_power_off: bool = False
    power_off_only: bool = False


def parse_launcher_cli(argv: list[str]) -> LauncherCli:
    """Parse launcher-specific flags from argv (including script/exe name)."""
    return LauncherCli(
        force_power_off=POWER_OFF_DISPLAY_FLAG in argv,
        power_off_only=POWER_OFF_ONLY_FLAG in argv,
    )
