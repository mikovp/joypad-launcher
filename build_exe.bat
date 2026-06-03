@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
    echo Python launcher ^(py^) not found.
    echo Install Python from https://www.python.org/downloads/
    echo and enable "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

py -3 -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo pip install failed.
    pause
    exit /b 1
)

py -3 -m PyInstaller --onefile --windowed --name JoypadLauncher --hidden-import scan_libraries --hidden-import covers --hidden-import cover_cdn --hidden-import ddcci --hidden-import input_remap --hidden-import input_remap_editor --collect-submodules ddcci --add-data "config.example.json;." --add-data "input_profiles;input_profiles" --add-data "assets;assets" --clean launcher.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Done: dist\JoypadLauncher.exe
echo Copy config.json or config.example.json to dist folder.
pause
