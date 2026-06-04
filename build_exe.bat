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

py -3 -m PyInstaller --onefile --windowed --name JoypadLauncher --collect-submodules joypad --collect-submodules ddcci --add-data "config.example.json;." --add-data "input_profiles;input_profiles" --add-data "assets;assets" --clean launcher.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo Packaging dist folder...
if not exist dist\input_profiles mkdir dist\input_profiles
xcopy /Y /Q input_profiles\*.json dist\input_profiles\ >nul
if exist bg.jpg copy /Y bg.jpg dist\ >nul
copy /Y config.example.json dist\ >nul
if not exist dist\config.json (
    copy /Y config.example.json dist\config.json >nul
    echo Created dist\config.json from config.example.json — edit before first run.
) else (
    echo Kept existing dist\config.json
)

echo.
echo Done: dist\JoypadLauncher.exe
echo Config: dist\config.json  Profiles: dist\input_profiles\
pause
