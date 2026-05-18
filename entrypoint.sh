#!/bin/bash
set -e

echo "🚀 Starting application and Cloudflare Tunnel..."

# Get the PORT from Railway or use default
PORT=${PORT:-8000}
echo "📦 Application will listen on port $PORT"

# Function to handle shutdown gracefully
cleanup() {
    echo "Shutting down..."
    kill $APP_PID $TUNNEL_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start FastAPI application in background
echo "🎯 Starting FastAPI application..."
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT &
APP_PID=$!

# Give the app time to start
sleep 3

# Start Cloudflare Tunnel in background (no authentication needed - quick tunnel mode)
echo "🌐 Starting Cloudflare Tunnel (quick mode, no auth)..."
cloudflared tunnel run --url http://localhost:$PORT &
TUNNEL_PID=$!

# Wait for both processes
wait $APP_PID $TUNNEL_PID
