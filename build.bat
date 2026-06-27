@echo off
title Solana Tracker - Build Standalone EXE
chcp 65001 > nul

echo ==============================================
echo        Solana Wallet Tracker EXE Builder       
echo ==============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ on Windows and try again.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist ".venv_win" (
    echo Creating virtual environment...
    python -m venv .venv_win
)

:: Activate virtual environment
echo Activating virtual environment...
call .venv_win\Scripts\activate

:: Install requirements and PyInstaller
echo Installing dependencies and PyInstaller...
pip install -r requirements.txt
pip install pyinstaller

:: Compile tracker.py
echo.
echo Compiling tracker.py...
pyinstaller --onefile --noconsole tracker.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to compile tracker.py
    pause
    exit /b 1
)

:: Compile configurator.py
echo.
echo Compiling configurator.py...
pyinstaller --onefile --noconsole --add-data ".venv_win\Lib\site-packages\flet\controls\material\icons.json;flet\controls\material" configurator.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to compile configurator.py
    pause
    exit /b 1
)

:: Create release directory structure
echo.
echo Creating release directory...
if not exist "release" (
    mkdir "release"
)
if not exist "release\secrets" (
    mkdir "release\secrets"
)

:: Move executables to release directory
echo.
echo Moving executables to release directory...
if exist "dist\tracker.exe" (
    move /y "dist\tracker.exe" "release\tracker.exe"
)
if exist "dist\configurator.exe" (
    move /y "dist\configurator.exe" "release\configurator.exe"
)

:: Copy example.env to release\secrets
if exist "example.env" (
    copy /y "example.env" "release\secrets\example.env"
)

:: Cleanup build files
echo.
echo Cleaning up build files...
rmdir /s /q build
rmdir /s /q dist
del /q tracker.spec
del /q configurator.spec

:: Delete Linux binary leftovers if they exist to keep Windows ZIP clean
if exist "release\tracker" del /f /q "release\tracker"
if exist "release\configurator" del /f /q "release\configurator"

:: Create ZIP archive using PowerShell
echo.
echo Creating release ZIP archive...
powershell -Command "Compress-Archive -Path 'release' -DestinationPath 'solana-wallet-tracker-windows.zip' -Force"

echo.
echo ==============================================
echo   Build Successful! 
echo   Generated release archive:
echo   - solana-wallet-tracker-windows.zip
echo   (Unzipping this file contains the release folder)
echo ==============================================
echo.
pause
