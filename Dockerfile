FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --default-timeout=1000 -r requirements.txt

COPY src ./src
COPY pyproject.toml .

RUN mkdir -p logs

EXPOSE 8000

# Start with PORT env var, default to 8000
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
