#!/bin/sh
# Railway sets $PORT dynamically; fallback to 8000 for local Docker
LISTEN_PORT="${PORT:-8000}"
echo "Starting uvicorn on port ${LISTEN_PORT}"
exec uvicorn src.main:app --host 0.0.0.0 --port "${LISTEN_PORT}"
