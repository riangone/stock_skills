#!/usr/bin/env bash
# start.sh — Start stock_skills WebUI (and optionally Docker services)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.webui.pid"
LOG_FILE="$SCRIPT_DIR/.webui.log"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"

cd "$SCRIPT_DIR"

# ── Check if already running ─────────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[stock_skills] WebUI is already running (PID $OLD_PID)"
        echo "  Use ./restart.sh to restart, or ./stop.sh to stop first."
        exit 1
    else
        echo "[stock_skills] Stale PID file found — cleaning up."
        rm -f "$PID_FILE"
    fi
fi

# ── Optional: start Docker services (Neo4j + TEI embedding) ──────────────────
if command -v docker &>/dev/null && [[ "${START_DOCKER:-1}" == "1" ]]; then
    echo "[stock_skills] Starting Docker services (Neo4j, TEI)..."
    docker compose up -d --quiet-pull 2>&1 | sed 's/^/  /' || true
fi

# ── Start WebUI ───────────────────────────────────────────────────────────────
echo "[stock_skills] Starting WebUI on http://$HOST:$PORT"
echo "  Log → $LOG_FILE"

nohup python3 -m uvicorn webui.app:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --no-access-log \
    >> "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "[stock_skills] WebUI started (PID $(cat "$PID_FILE"))"
