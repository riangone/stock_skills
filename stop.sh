#!/usr/bin/env bash
# stop.sh — Stop stock_skills WebUI (and optionally Docker services)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.webui.pid"

cd "$SCRIPT_DIR"

# ── Stop WebUI ────────────────────────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "[stock_skills] Stopping WebUI (PID $PID)..."
        kill "$PID"
        # Wait up to 10 seconds for graceful shutdown
        for i in $(seq 1 10); do
            kill -0 "$PID" 2>/dev/null || break
            sleep 1
        done
        if kill -0 "$PID" 2>/dev/null; then
            echo "[stock_skills] Process did not exit — sending SIGKILL."
            kill -9 "$PID" || true
        fi
        rm -f "$PID_FILE"
        echo "[stock_skills] WebUI stopped."
    else
        echo "[stock_skills] PID $PID is no longer running — cleaning up."
        rm -f "$PID_FILE"
    fi
else
    echo "[stock_skills] No PID file found. WebUI may not be running."
fi

# ── Optional: stop Docker services ───────────────────────────────────────────
if command -v docker &>/dev/null && [[ "${STOP_DOCKER:-0}" == "1" ]]; then
    echo "[stock_skills] Stopping Docker services..."
    docker compose down 2>&1 | sed 's/^/  /' || true
fi
