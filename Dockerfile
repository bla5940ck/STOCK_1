FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev python3-dev \
    libglib2.0-0 libsm6 libxrender1 libxext6 libx11-6 \
    fonts-liberation libnss3 libappindicator3-1 libindicator7 xdg-utils && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --default-timeout=1000 -r requirements.txt && \
    playwright install chromium

COPY src ./src
COPY pyproject.toml .

RUN mkdir -p logs

EXPOSE 8000

CMD python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
