#!/bin/bash

echo "=============================================="
echo "      Solana Wallet Tracker Bot Launcher      "
echo "=============================================="
echo

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment."
    exit 1
fi

# Install dependencies
echo "Checking and installing requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    exit 1
fi

# Check if tkinter is available and if we want GUI mode
GUI_SUPPORTED=0
if python3 -c "import tkinter" &>/dev/null; then
    GUI_SUPPORTED=1
fi

# Support a bot-only flag
BOT_ONLY=0
for arg in "$@"; do
    if [ "$arg" == "--bot-only" ] || [ "$arg" == "-b" ]; then
        BOT_ONLY=1
    fi
done

if [ $GUI_SUPPORTED -eq 1 ] && [ $BOT_ONLY -eq 0 ]; then
    # Start the configurator GUI
    echo "Starting Configuration Panel..."
    python3 configurator.py
else
    # Fallback/Direct run
    if [ $BOT_ONLY -eq 0 ]; then
        echo "[WARNING] Tkinter (GUI library) is not installed in this Linux/WSL environment."
        echo "To run the GUI, install it using: sudo apt install python3-tk"
        echo "Falling back to running the Tracker Bot directly..."
        echo "----------------------------------------------"
    else
        echo "Starting Solana Wallet Tracker Bot directly (bot-only mode)..."
        echo "----------------------------------------------"
    fi
    python3 tracker.py
fi
