#!/usr/bin/env bash
set -e

echo ""
echo "  ============================"
echo "    Pinedit - Photo Editor"
echo "  ============================"
echo ""

# Check for Python
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "[ERROR] Python is not installed."
    echo "Please install Python 3.9+ from https://python.org"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    $PY -m venv venv
else
    echo "[1/3] Virtual environment found."
fi

# Activate venv and install dependencies
echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet

# Launch the app
echo "[3/3] Starting Pinedit..."
echo ""
echo "  App running at: http://localhost:5000"
echo "  Press Ctrl+C to stop."
echo ""

# Open browser (works on macOS and Linux)
if command -v open &>/dev/null; then
    open http://localhost:5000 &
elif command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5000 &
fi

# Run Flask
python app.py
