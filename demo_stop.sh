#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
#  demo_stop.sh — Cleanly stop all demo processes
#
#  Kills (in order):
#    1. ngrok tunnel
#    2. Frontend dev server
#    3. Backend
#
#  Usage:
#    ./demo_stop.sh
# =============================================================================

cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)
echo ""
echo "=============================================="
echo "   RTL2GDS AGENT — DEMO STOP"
echo "=============================================="
echo ""

# Read PIDs from files (fallback: search by port)
BACKEND_PID=""
NGROK_PID=""
FRONTEND_PID=""

if [ -f .demo_backend.pid ]; then
    BACKEND_PID=$(cat .demo_backend.pid)
fi
if [ -f .demo_ngrok.pid ]; then
    NGROK_PID=$(cat .demo_ngrok.pid)
fi
if [ -f .demo_frontend.pid ]; then
    FRONTEND_PID=$(cat .demo_frontend.pid)
fi

# Stop ngrok
if [ -n "$NGROK_PID" ] && kill -0 "$NGROK_PID" 2>/dev/null; then
    echo "[1/3] Stopping ngrok (PID $NGROK_PID)..."
    kill "$NGROK_PID" 2>/dev/null || true
    sleep 1
    echo "       done."
else
    echo "[1/3] Stopping ngrok..."
    pkill -f "ngrok http 8000" 2>/dev/null || true
    echo "       done (searched by process name)."
fi

# Stop frontend
if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "[2/3] Stopping frontend (PID $FRONTEND_PID)..."
    kill "$FRONTEND_PID" 2>/dev/null || true
    sleep 1
    echo "       done."
else
    echo "[2/3] Stopping frontend..."
    fuser -k 3000/tcp 2>/dev/null || true
    echo "       done (searched by port)."
fi

# Stop backend
if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "[3/3] Stopping backend (PID $BACKEND_PID)..."
    kill "$BACKEND_PID" 2>/dev/null || true
    sleep 1
    echo "       done."
else
    echo "[3/3] Stopping backend..."
    fuser -k 8000/tcp 2>/dev/null || true
    echo "       done (searched by port)."
fi

# Clean up PID files
rm -f .demo_backend.pid .demo_ngrok.pid .demo_frontend.pid .demo_ngrok_url.txt

# Give processes time to release ports
sleep 1

echo ""
echo "All processes stopped."
echo ""

# Final check — warn if anything is still listening
STILL_RUNNING=false
for port in 8000 3000 4040; do
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "[WARN] Port $port is still in use. Forcing kill..."
        fuser -k "${port}/tcp" 2>/dev/null || true
        sleep 1
        if ss -tlnp 2>/dev/null | grep -q ":$port "; then
            echo "       Port $port still bound — check manually: fuser -k $port/tcp"
            STILL_RUNNING=true
        fi
    fi
done

if [ "$STILL_RUNNING" = false ]; then
    echo "All ports free."
fi
echo "Done."
