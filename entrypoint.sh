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

# Start Cloudflare Tunnel in background (only if TUNNEL_TOKEN is set)
if [ -n "$TUNNEL_TOKEN" ]; then
    echo "🌐 Starting Cloudflare Tunnel..."
    cloudflared tunnel run &
    TUNNEL_PID=$!
else
    echo "⚠️  TUNNEL_TOKEN not set - Tunnel will not start (local mode only)"
    TUNNEL_PID=""
fi

# Wait for both processes
if [ -n "$TUNNEL_PID" ]; then
    wait $APP_PID $TUNNEL_PID
else
    wait $APP_PID
fi
