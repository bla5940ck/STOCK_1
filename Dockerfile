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

EXPOSE 3000

# Try port 3000 (Railway default)
CMD exec uvicorn test_app:app --host 0.0.0.0 --port 3000
