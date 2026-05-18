#!/bin/sh
set -e

# Debug: Print environment
echo "====== STARTUP DEBUG ======"
echo "PORT env var: ${PORT}"
echo "======== END DEBUG ========"

echo "Starting uvicorn on port 3000"
exec python -m uvicorn test_app:app --host 0.0.0.0 --port 3000
