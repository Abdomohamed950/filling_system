#!/bin/bash

# Check if pip is installed, if not, install it
if ! command -v pip &> /dev/null; then
    echo "pip not found. Installing pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

VENV_DIR="$HOME/venv_filling_system"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install -r requirements.txt

python3 src/main.py