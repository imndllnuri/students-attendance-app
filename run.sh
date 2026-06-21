#!/usr/bin/env bash
# Sets up the environment (if needed), starts the Flask backend, then launches
# the PyQt5 desktop client. Stops the backend when the client exits.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install -q -r requirements.txt

echo "Starting backend server..."
python3 -m server.app &
SERVER_PID=$!

cleanup() {
    echo "Stopping backend server..."
    kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Give the server a moment to come up before the GUI tries to talk to it.
sleep 1

echo "Launching desktop app..."
python3 main.py
