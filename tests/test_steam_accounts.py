"""Tests for Steam account discovery."""

import os

from joypad.games.model import build_categorized_game_list, build_tile_sections
from joypad.integrations.steam.accounts import (
    active_steam_login,
    get_active_steam_account,
    read_steam_accounts,
)


def _write_loginusers(steam_dir, users_vdf_body):
    config_dir = os.path.join(steam_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    path = os.path.join(config_dir, "loginusers.vdf")
    with open(path, "w", encoding="utf-8") as f:
        f.write(users_vdf_body)


def test_read_steam_accounts_and_active(tmp_path):
    steam_dir = str(tmp_path)
    _write_loginusers(
        steam_dir,
        '''
"users"
{
    "76561198000000001"
    {
        "AccountName" "alice"
        "PersonaName" "AliceDisplay"
        "MostRecent" "0"
    }
    "76561198000000002"
    {
        "AccountName" "bob"
        "PersonaName" "BobDisplay"
        "MostRecent" "1"
    }
}
''',
    )
    accounts = read_steam_accounts(steam_dir)
    assert len(accounts) == 2
    active = get_active_steam_account(steam_dir)
    assert active["account_name"] == "bob"
    assert active_steam_login(active) == "bob"


def test_active_steam_login_falls_back_to_persona():
    assert active_steam_login({"account_name": "", "persona_name": "Nick"}) == "Nick"
    assert active_steam_login(None) is None


def test_steam_section_title_includes_login():
    games = [{"name": "Half-Life", "platform": "steam"}]
    items = build_categorized_game_list(games, "mylogin")
    assert items[0]["title"] == "Steam: mylogin"
    secs = build_tile_sections(games, "mylogin")
    assert secs[0]["title"] == "Steam: mylogin"
