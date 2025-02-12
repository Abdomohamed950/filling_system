#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

VENV_DIR="$HOME/venv_filling_system"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
fi

if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Failed to create virtual environment."
    exit 1
fi

if command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    echo "pip not found in the virtual environment."
    exit 1
fi

if [ -f "src/main.py" ]; then
    python3 src/main.py
else
    echo "src/main.py not found."
    exit 1
fi