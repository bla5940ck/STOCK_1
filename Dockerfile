FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Test app - minimal dependency
RUN pip install --upgrade pip && pip install fastapi uvicorn

COPY test_app.py .

EXPOSE 8000

# Start test app with PORT env var, default to 8000
CMD exec uvicorn test_app:app --host 0.0.0.0 --port ${PORT:-8000}
