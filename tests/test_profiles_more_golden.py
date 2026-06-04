import os
import shutil

from joypad.input import profiles as p

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PROFILE_SRC = os.path.join(
    REPO_ROOT, "input_profiles", "default_wasd_mouse.json"
)


def test_merge_profiles_override_wins_and_shallow_nested():
    base = {"a": 1, "nested": {"x": 1, "y": 2}, "keep": 5}
    override = {"a": 9, "nested": {"y": 20, "z": 30}, "new": 7}
    merged = p.merge_profiles(base, override)
    # top-level: override wins, base-only key preserved, override-only key added
    assert merged["a"] == 9
    assert merged["keep"] == 5
    assert merged["new"] == 7
    # nested dicts are SHALLOW-merged (dict.update): base-only nested key kept,
    # override nested keys win/added.
    assert merged["nested"] == {"x": 1, "y": 20, "z": 30}
    # base is not mutated
    assert base["nested"] == {"x": 1, "y": 2}


def test_ensure_chords_completes_partial():
    prof = {"chords": {"lb": {"a": "space"}}}
    chords = p.ensure_chords(prof)
    assert set(chords.keys()) == {"lb", "rb"}
    # existing partial key preserved, missing numeric face keys filled with "none"
    assert chords["lb"] == {"a": "space", "0": "none", "1": "none", "2": "none", "3": "none"}
    assert chords["rb"] == {"0": "none", "1": "none", "2": "none", "3": "none"}


def test_ensure_chords_on_empty_profile():
    chords = p.ensure_chords({})
    assert chords == {
        "lb": {"0": "none", "1": "none", "2": "none", "3": "none"},
        "rb": {"0": "none", "1": "none", "2": "none", "3": "none"},
    }


def test_default_profile_top_level_keys(tmp_path):
    base = tmp_path / "base"
    (base / "input_profiles").mkdir(parents=True)
    shutil.copy(DEFAULT_PROFILE_SRC, base / "input_profiles" / "default_wasd_mouse.json")
    prof = p.default_profile(name="Custom", base_dir=str(base))
    expected = {
        "name",
        "left_stick",
        "right_stick",
        "buttons",
        "triggers",
        "dpad",
        "chords",
        "stick_clicks",
    }
    assert expected <= set(prof.keys())
    assert prof["name"] == "Custom"


def test_assign_and_unassign_round_trip(tmp_path):
    base = tmp_path / "base"
    (base / "input_profiles").mkdir(parents=True)
    shutil.copy(DEFAULT_PROFILE_SRC, base / "input_profiles" / "default_wasd_mouse.json")
    config = {}
    game = {"platform": "steam", "steam_app_id": "440", "name": "TF2"}
    key = p.game_remap_key(game)

    p.assign_game_profile(config, game, "tf2_prof", str(base))
    assert config["input_remap_games"][key] == "tf2_prof"
    # assign creates the profile file on disk under base_dir
    assert (base / "input_profiles" / "tf2_prof.json").is_file()

    p.unassign_game(config, game)
    assert key not in config["input_remap_games"]


def test_suggest_profile_id_slug_and_stable():
    game = {"name": "Half-Life 2!"}
    first = p.suggest_profile_id(game)
    assert isinstance(first, str)
    assert first
    assert first == "half_life_2"
    # stable for same input
    assert p.suggest_profile_id(game) == first
    # empty name falls back to a non-empty default
    assert p.suggest_profile_id({}) == "game"


def test_game_remap_key_deterministic():
    steam = {"platform": "steam", "steam_app_id": "440"}
    assert p.game_remap_key(steam) == "steam:440"
    assert p.game_remap_key(steam) == "steam:440"
    assert p.game_remap_key({"platform": "other", "name": "My Game"}) == "name:My Game"
    assert p.game_remap_key({}) == ""
