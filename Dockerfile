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

# Copy and set up entrypoint script
COPY start.sh .
# Fix CRLF line endings (Windows) and make executable
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Run application via entrypoint script
# PORT env var is set by Railway automatically; fallback to 8000 for local
CMD ["/app/start.sh"]
