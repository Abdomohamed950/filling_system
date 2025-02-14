#!/bin/bash

VENV_DIR="$HOME/venv_filling_system"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install -r requirements.txt

python3 src/main.py