#!/bin/bash
# START_JARVIS_MAC_LINUX.sh
# One-click launcher for JARVIS (Mark LV) on macOS and Linux

echo ""
echo " =========================================="
echo "  JARVIS (Mark LV) - Quick Start"
echo " =========================================="
echo ""

# Move to project root (one level up from this script's folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Detect python command
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "[ERROR] Python is not installed or not on PATH."
    echo "        Install Python 3.11-3.13 from https://python.org"
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[INFO] Found Python $PY_VERSION"

# Run setup if this is the first launch (no config file yet)
if [ ! -f "config/api_keys.json" ]; then
    echo "[INFO] First run detected — running setup..."
    $PYTHON setup.py
    if [ $? -ne 0 ]; then
        echo "[ERROR] Setup failed. See error above."
        exit 1
    fi
    echo ""
fi

echo "[INFO] Starting JARVIS..."
echo "       Hold Ctrl+Space to speak."
echo "       Say 'Hey Jarvis' if wake word is enabled."
echo ""
$PYTHON main.py
