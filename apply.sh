#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ -d "$ROOT/.venv" ]; then
    echo "[*] Activating virtual environment..."
    source "$ROOT/.venv/bin/activate"
fi

if ! command -v paletteflow &>/dev/null; then
    if [ -f "$ROOT/pyproject.toml" ]; then
        echo "[*] Installing paletteflow in editable mode..."
        pip install -e "$ROOT" --quiet
    else
        echo "Error: paletteflow not installed and pyproject.toml not found." >&2
        exit 1
    fi
fi

echo "[*] Running PaletteFlow full pipeline..."
paletteflow apply
