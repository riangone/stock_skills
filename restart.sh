#!/usr/bin/env bash
# restart.sh — Restart stock_skills WebUI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

echo "[stock_skills] Restarting WebUI..."
bash "$SCRIPT_DIR/stop.sh"
sleep 1
bash "$SCRIPT_DIR/start.sh"
