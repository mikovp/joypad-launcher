@echo off
pip install pyinstaller --quiet
python -m PyInstaller --onefile --windowed --name JoypadLauncher --hidden-import scan_libraries --add-data "config.example.json;." --clean launcher.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)
echo.
echo Done: dist\JoypadLauncher.exe
echo Copy config.json or config.example.json to dist folder.
pause
