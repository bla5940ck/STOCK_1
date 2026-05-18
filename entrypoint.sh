#!/bin/sh
set -e

# Debug: Print environment
echo "====== STARTUP DEBUG ======"
echo "PORT env var: ${PORT}"
echo "======== END DEBUG ========"

# If PORT not set, use 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port: $PORT"
exec python -m uvicorn test_app:app --host 0.0.0.0 --port "$PORT"
