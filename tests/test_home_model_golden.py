from joypad.ui.views.home.model import build_home_shelves


def _g(name, plat):
    return {"name": name, "platform": plat}


def test_shelves_are_sources_then_all():
    sections = [
        {"title": "Steam", "games": [_g("Hades", "steam"), _g("Celeste", "steam")]},
        {"title": "Epic Games", "games": [_g("Alan Wake", "epic")]},
    ]
    shelves = build_home_shelves(sections)
    assert [s["title"] for s in shelves] == ["Steam", "Epic Games", "All"]
    # "All" shelf sorted case-insensitively by name
    assert [g["name"] for g in shelves[-1]["games"]] == ["Alan Wake", "Celeste", "Hades"]


def test_empty_sections_dropped():
    sections = [
        {"title": "Steam", "games": []},
        {"title": "Epic Games", "games": [_g("Alan Wake", "epic")]},
    ]
    shelves = build_home_shelves(sections)
    assert [s["title"] for s in shelves] == ["Epic Games", "All"]


def test_no_games_returns_empty():
    assert build_home_shelves([{"title": "Steam", "games": []}]) == []
    assert build_home_shelves([]) == []
