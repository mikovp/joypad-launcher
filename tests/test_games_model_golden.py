from joypad.games import model as launcher

GAMES = [
    {"name": "HL2", "platform": "steam"},
    {"name": "RL", "platform": "epic"},
    {"name": "Z", "platform": "twitch", "nsp_filename": "Zelda.nsp"},
    {"name": "Legacy", "platform": "nsp", "nsp_filename": "Mario.nsp"},
    {"name": "Mystery", "platform": "weird"},
]


def test_game_sections_order_and_omission():
    sections = launcher._game_sections(GAMES)
    titles = [t for t, _ in sections]
    assert titles == ["Steam", "Epic Games", "Twitch", "Other"]
    twitch_names = [g["name"] for title, lst in sections if title == "Twitch" for g in lst]
    assert twitch_names == ["Z", "Legacy"]
    assert launcher._game_sections([{"name": "A", "platform": "steam"}]) == \
        [("Steam", [{"name": "A", "platform": "steam"}])]


def test_build_categorized_game_list_headers_then_games():
    items = launcher.build_categorized_game_list(
        [{"name": "A", "platform": "steam"}]
    )
    assert items[0] == {"kind": "header", "title": "Steam"}
    assert items[1]["kind"] == "game"
    assert items[1]["game"]["name"] == "A"


def test_build_tile_sections_shape():
    secs = launcher.build_tile_sections([{"name": "A", "platform": "epic"}])
    assert secs == [{"title": "Epic Games", "games": [{"name": "A", "platform": "epic"}]}]


def test_tile_selection_title_twitch_prefers_filename():
    g = {"name": "X", "platform": "twitch", "nsp_filename": "Zelda.nsp", "nsp_path": r"C:\a.nsp"}
    assert launcher.tile_selection_title(g) == "Zelda.nsp"
