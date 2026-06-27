#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
#  demo.sh — Hackathon Demo Launcher
#
#  Starts:
#    1. Backend (PIPELINE_MODE=real) on port 8000
#    2. ngrok tunnel exposing port 8000 to a public URL
#    3. Frontend dev server on port 3000, pointed at the ngrok URL
#
#  Prints:
#    - Local frontend URL (http://localhost:3000)
#    - Public ngrok tunnel URL for the backend API
#    - Instructions for the demo
#
#  Usage:
#    chmod +x demo.sh
#    ./demo.sh
#
#  Stop:
#    ./demo_stop.sh
# =============================================================================

cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)
echo ""
echo "=============================================="
echo "   RTL2GDS AGENT — HACKATHON DEMO LAUNCHER"
echo "=============================================="
echo ""

# ---------------------------------------------------------------------------
# Activate virtual environment
# ---------------------------------------------------------------------------
if [ ! -f .venv/bin/activate ]; then
    echo "[FAIL] Virtual environment not found at .venv/bin/activate"
    echo "       Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
source .venv/bin/activate

# ---------------------------------------------------------------------------
# Kill any leftover processes from previous runs
# ---------------------------------------------------------------------------
echo "[1/5] Cleaning up old processes..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
pkill -f "ngrok http 8000" 2>/dev/null || true
sleep 1
echo "       done."

# ---------------------------------------------------------------------------
# Start the backend
# ---------------------------------------------------------------------------
echo "[2/5] Starting backend (PIPELINE_MODE=real)..."
mkdir -p logs
PIPELINE_MODE=real nohup python -m ui.backend.main > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "       PID $BACKEND_PID — logs/backend.log"

# Wait for backend to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "       Backend ready on http://localhost:8000"
        break
    fi
    if [ "$i" -eq 15 ]; then
        echo "[FAIL] Backend failed to start within 15 seconds"
        echo "       Check logs/backend.log"
        exit 1
    fi
    sleep 1
done

# ---------------------------------------------------------------------------
# Start ngrok tunnel
# ---------------------------------------------------------------------------
echo "[3/5] Starting ngrok tunnel..."

# Find ngrok binary
NGROK=""
for candidate in ~/bin/ngrok /usr/local/bin/ngrok /snap/bin/ngrok; do
    if [ -x "$candidate" ]; then
        NGROK="$candidate"
        break
    fi
done
if [ -z "$NGROK" ]; then
    echo "[FAIL] ngrok not found. Install via:"
    echo "       curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz"
    echo "       tar xzf /tmp/ngrok.tgz -C ~/bin/"
    exit 1
fi
echo "       Using ngrok: $NGROK"

$NGROK http 8000 --log=stdout > logs/ngrok.log 2>&1 &
NGROK_PID=$!
echo "       PID $NGROK_PID — logs/ngrok.log"

# Wait for ngrok to allocate a tunnel URL
NGROK_URL=""
for i in $(seq 1 20); do
    sleep 1
    API_RESP=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null || echo '{"tunnels":[]}')
    NGROK_URL=$(echo "$API_RESP" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tunnels = [t['public_url'] for t in d.get('tunnels', []) if t.get('public_url', '').startswith('https://')]
    print(tunnels[0] if tunnels else '')
except Exception:
    print('')
" 2>/dev/null || echo "")
    if [ -n "$NGROK_URL" ]; then
        echo "       Tunnel ready: $NGROK_URL"
        break
    fi
done

if [ -z "$NGROK_URL" ]; then
    echo "[FAIL] ngrok did not allocate a tunnel URL within 20 seconds"
    echo "       Check logs/ngrok.log"
    echo "       Make sure you have an ngrok authtoken configured:"
    echo "         ~/bin/ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

# ---------------------------------------------------------------------------
# Start the frontend
# ---------------------------------------------------------------------------
echo "[4/5] Starting frontend (pointed at ngrok tunnel)..."
cd ui/frontend

# Install dependencies if missing
if [ ! -d node_modules ]; then
    echo "       Installing frontend dependencies..."
    pnpm install > /dev/null 2>&1
fi

NEXT_PUBLIC_API_BASE_URL="$NGROK_URL" nohup pnpm dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"
echo "       PID $FRONTEND_PID — logs/frontend.log"

# Wait for frontend to be ready
for i in $(seq 1 20); do
    if curl -s -o /dev/null -w "" http://localhost:3000/dashboard 2>/dev/null; then
        echo "       Frontend ready on http://localhost:3000"
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo "[WARN] Frontend may not be ready — check logs/frontend.log"
    fi
    sleep 1
done

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
echo ""
echo "[5/5] =============================================="
echo "            DEMO READY"
echo "=============================================="
echo ""
echo "   Frontend (local):"
echo "     http://localhost:3000"
echo "     (the API already points to the ngrok tunnel)"
echo ""
echo "   Backend API (via ngrok):"
echo "     $NGROK_URL"
echo ""
echo "   ngrok admin panel:"
echo "     http://localhost:4040"
echo ""
echo "   Vercel production frontend (if deployed):"
echo "     https://frontend-pi-one-67.vercel.app"
echo ""
echo "   Demo tips:"
echo "     • Open http://localhost:3000 and run alu_8bit"
echo "     • The backend runs REAL Icarus Verilog + cocotb"
echo "     • Share the ngrok URL for remote API access"
echo "     • Monitor logs:  tail -f logs/backend.log"
echo ""
echo "   To stop:  ./demo_stop.sh"
echo "=============================================="
echo ""

# Save PIDs for the stop script
echo "$BACKEND_PID" > .demo_backend.pid
echo "$NGROK_PID" > .demo_ngrok.pid
echo "$FRONTEND_PID" > .demo_frontend.pid
echo "$NGROK_URL" > .demo_ngrok_url.txt
