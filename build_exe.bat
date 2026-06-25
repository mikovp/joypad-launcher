@echo off

setlocal

cd /d "%~dp0"



echo Stopping running Joypad Launcher / Starter processes...

taskkill /IM JoypadLauncher.exe /F >nul 2>&1

taskkill /IM JoypadStarter.exe /F >nul 2>&1

timeout /t 1 /nobreak >nul



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



if exist dist\JoypadStarter.exe del /F /Q dist\JoypadStarter.exe >nul 2>&1



echo Building JoypadStarter ^(onedir, headless, no pygame^)...

py -3 -m PyInstaller --noconfirm --onedir --windowed --name JoypadStarter --exclude-module pygame --collect-submodules joypad.starter --collect-submodules joypad.input.xinput --clean starter.py

if errorlevel 1 (

    echo JoypadStarter build failed.

    pause

    exit /b 1

)



echo Building JoypadLauncher.exe...

py -3 -m PyInstaller --noconfirm --onefile --windowed --name JoypadLauncher --collect-submodules joypad --collect-submodules ddcci --add-data "config.example.json;." --add-data "input_profiles;input_profiles" --add-data "assets;assets" --clean launcher.py

if errorlevel 1 (

    echo JoypadLauncher build failed.

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

    echo Created dist\config.json from config.example.json - edit before first run.

) else (

    echo Kept existing dist\config.json

)



echo.

echo Done:

echo   dist\JoypadLauncher.exe           - game UI

echo   dist\JoypadStarter\JoypadStarter.exe - background Back+Start listener

echo Config: dist\config.json  Profiles: dist\input_profiles\



reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v JoypadLauncherGamepadStarter >nul 2>&1

if not errorlevel 1 (

    if exist dist\JoypadStarter\JoypadStarter.exe (

        taskkill /IM JoypadStarter.exe /F >nul 2>&1

        timeout /t 1 /nobreak >nul

        echo Restarting JoypadStarter ^(Back+Start listener was enabled^)...

        start "" /B dist\JoypadStarter\JoypadStarter.exe

    )

)



pause


