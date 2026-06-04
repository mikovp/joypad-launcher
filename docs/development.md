# Development

## Requirements

- Python 3.8+
- Windows (for Steam/Epic/remap worker)
- Runtime: `requirements.txt`
- Dev: `requirements-dev.txt` (pytest, ruff, mypy)

## Run from source

```bash
pip install -r requirements-dev.txt
copy config.example.json config.json
python launcher.py
```

## Tests and linters

```bash
python -m pytest -q
python -m ruff check .
python -m mypy joypad/config/types.py joypad/config/twitch.py
```

## Build EXE

```bash
build_exe.bat
```

Output: `dist\JoypadLauncher.exe`. Copy `config.json` next to the exe.

## Entry point

`launcher.py` calls `joypad.app.main()`. Remap worker: `--input-remap-worker` flag (see `joypad.input.worker`).

## Module map

See [architecture.md](architecture.md).
