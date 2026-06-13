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
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

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
pyinstaller --onefile --noconsole configurator.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to compile configurator.py
    pause
    exit /b 1
)

:: Move executables to root directory
echo.
echo Moving executables to root directory...
if exist "dist\tracker.exe" (
    move /y "dist\tracker.exe" "tracker.exe"
)
if exist "dist\configurator.exe" (
    move /y "dist\configurator.exe" "configurator.exe"
)

:: Cleanup build files
echo.
echo Cleaning up build files...
rmdir /s /q build
rmdir /s /q dist
del /q tracker.spec
del /q configurator.spec

echo.
echo ==============================================
echo   Build Successful! 
echo   Generated files:
echo   - configurator.exe (Configuration Panel GUI)
echo   - tracker.exe      (Background Bot Worker)
echo.
echo   You can copy the entire "telegramcrypt" folder
echo   to your friend's PC. They only need to run
echo   "configurator.exe" - no Python required!
echo ==============================================
echo.
pause
