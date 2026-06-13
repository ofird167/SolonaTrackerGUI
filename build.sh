#!/bin/bash

echo "=============================================="
echo "      Solana Wallet Tracker Linux Builder     "
echo "=============================================="
echo

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements and PyInstaller
echo "Installing dependencies and PyInstaller..."
pip install -r requirements.txt
pip install pyinstaller

# Compile tracker.py
echo
echo "Compiling tracker.py..."
pyinstaller --onefile --noconsole tracker.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to compile tracker.py"
    exit 1
fi

# Compile configurator.py
echo
echo "Compiling configurator.py..."
pyinstaller --onefile --noconsole configurator.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to compile configurator.py"
    exit 1
fi

# Create release directory structure
echo
echo "Creating release directory..."
mkdir -p release/secrets

# Move executables to release directory
echo
echo "Moving executables to release directory..."
if [ -f "dist/tracker" ]; then
    mv -f dist/tracker release/tracker
fi
if [ -f "dist/configurator" ]; then
    mv -f dist/configurator release/configurator
fi

# Copy example.env to release/secrets
if [ -f "example.env" ]; then
    cp -f example.env release/secrets/example.env
fi

# Cleanup build files
echo
echo "Cleaning up build files..."
rm -rf build dist tracker.spec configurator.spec

echo
echo "=============================================="
echo "   Build Successful!"
echo "   Generated files in \"release\" folder:"
echo "   - release/configurator (Configuration Panel GUI)"
echo "   - release/tracker      (Background Bot Worker)"
echo "   - release/secrets/example.env"
echo
echo "   You can tar/zip and copy the \"release\" folder."
echo "   Users only need to run \"configurator\"!"
echo "=============================================="
echo
