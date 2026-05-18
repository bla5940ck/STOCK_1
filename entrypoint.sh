#!/bin/bash
set -e

echo "🚀 Starting FastAPI application..."

# Get the PORT from Railway or use default
PORT=${PORT:-8000}
echo "📦 Application will listen on port $PORT"

# Start FastAPI application
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
