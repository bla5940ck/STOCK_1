FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with retry
RUN pip install --upgrade pip setuptools wheel && \
    pip install --default-timeout=1000 -r requirements.txt || \
    pip install --default-timeout=1000 -r requirements.txt

# Copy application code
COPY src ./src
COPY pyproject.toml .

# Create logs directory
RUN mkdir -p logs

# Health check (use python since curl is not installed in slim image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:' + __import__('os').environ.get('PORT','8000') + '/health')"

# Run application (PORT env var is set by Railway, fallback to 8000 for local)
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
