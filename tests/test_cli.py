from joypad.cli import (
    POWER_OFF_DISPLAY_FLAG,
    POWER_OFF_ONLY_FLAG,
    LauncherCli,
    parse_launcher_cli,
)


def test_parse_launcher_cli_defaults():
    assert parse_launcher_cli(["JoypadLauncher.exe"]) == LauncherCli()


def test_parse_launcher_cli_force_power_off():
    argv = ["JoypadLauncher.exe", POWER_OFF_DISPLAY_FLAG]
    assert parse_launcher_cli(argv) == LauncherCli(force_power_off=True)


def test_parse_launcher_cli_power_off_only():
    argv = ["JoypadLauncher.exe", POWER_OFF_ONLY_FLAG]
    assert parse_launcher_cli(argv) == LauncherCli(power_off_only=True)


def test_parse_launcher_cli_both_flags():
    argv = ["JoypadLauncher.exe", POWER_OFF_DISPLAY_FLAG, POWER_OFF_ONLY_FLAG]
    cli = parse_launcher_cli(argv)
    assert cli.force_power_off is True
    assert cli.power_off_only is True
