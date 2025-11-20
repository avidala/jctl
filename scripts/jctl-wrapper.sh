#!/usr/bin/env bash
# jctl wrapper script - automatically activates venv and runs jctl

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Run: cd $PROJECT_DIR && python3 -m venv venv && pip install -e ."
    exit 1
fi

# Activate venv and run jctl with all arguments
source "$VENV_DIR/bin/activate"
exec python3 -m jctl "$@"
