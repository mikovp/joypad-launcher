import json
import os
import sys

from joypad.paths import _BASE_DIR, CONFIG_EXAMPLE, CONFIG_PATH


def load_config():
    """Loads config.json or uses example and exits if not found."""
    path = CONFIG_PATH
    if not os.path.exists(path):
        path = CONFIG_EXAMPLE
    if not os.path.exists(path) and getattr(sys, "frozen", False):
        path_mei = os.path.join(sys._MEIPASS, "config.example.json")
        if os.path.exists(path_mei):
            path = path_mei
    if not os.path.exists(path):
        msg = f"config.json not found. Copy config.example.json to the launcher folder:\n{_BASE_DIR}"
        print(msg)
        raise FileNotFoundError(msg)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if path == CONFIG_EXAMPLE and not os.path.exists(CONFIG_PATH):
        print("Using config.example.json. Copy to config.json and configure games.")
    return data


def save_config(data):
    """Writes config to config.json next to launcher/exe."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
