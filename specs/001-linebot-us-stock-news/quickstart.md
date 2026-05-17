# Quick Start Guide: LINE Bot 美股與新聞助理

**Date**: 2026-05-17  
**Version**: 1.0.0  
**Target Audience**: Developers

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Project Structure Overview](#project-structure-overview)
4. [Running the Bot](#running-the-bot)
5. [Testing & Validation](#testing--validation)
6. [Webhook Configuration](#webhook-configuration)
7. [Debugging & Troubleshooting](#debugging--troubleshooting)
8. [Deployment](#deployment)

---

## Prerequisites

### Required Software

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/)
- **Docker** (Optional, for containerized deployment) - [Download](https://www.docker.com/)
- **LINE Messaging API Account** - [Setup](https://developers.line.biz/en/)
- **VS Code** (Recommended) - [Download](https://code.visualstudio.com/)

### Required Accounts & API Keys

1. **LINE Bot Channel** (Free)
   - Visit: https://developers.line.biz/
   - Create a Messaging API Channel
   - Get: `CHANNEL_ACCESS_TOKEN`, `CHANNEL_SECRET`

2. **Yahoo Finance** (Free, no API key needed)
   - No registration required
   - Uses `yfinance` Python library

3. **Alpha Vantage** (Optional, Free tier)
   - Visit: https://www.alphavantage.co/
   - Get: `ALPHA_VANTAGE_API_KEY`
   - Rate limit: 5 calls/minute

### System Requirements

- **RAM**: ≥4 GB
- **Disk**: ≥2 GB
- **Network**: Internet connection for API calls
- **OS**: Windows, macOS, or Linux (Ubuntu 20.04+ recommended)

---

## Local Development Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/linebot-us-stock.git
cd linebot-us-stock
```

### Step 2: Create a Virtual Environment

**On macOS/Linux**:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell)**:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key packages**:
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `line-bot-sdk==3.4.0` - LINE Messaging API SDK
- `aiohttp==3.9.1` - Async HTTP client
- `yfinance==0.2.32` - Yahoo Finance data
- `feedparser==6.0.10` - RSS news parsing
- `sqlalchemy==2.0.23` - Database ORM
- `pydantic==2.5.0` - Data validation
- `pytest==7.4.3` - Testing
- `pytest-asyncio==0.21.1` - Async testing

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here

# API Keys (Optional)
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# Database Configuration (SQLite for dev)
DATABASE_URL=sqlite:///./linebot_stock.db

# Webhook Configuration
WEBHOOK_URL=https://your-domain.com/webhook/line
```

**⚠️ IMPORTANT**: Never commit `.env` to git. Use `.env.example` template for version control.

```bash
# Create .env.example for team members
cp .env .env.example
# Edit .env.example to remove sensitive values
```

### Step 5: Initialize Database

```bash
python -m src.db.database init
```

This creates:
- SQLite database file (`linebot_stock.db`)
- Required tables (indices, stocks, news, etc.)
- Initial Taiwan stock correlation data

---

## Project Structure Overview

```
linebot-us-stock/
├── src/
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration management (env vars)
│   ├── api/
│   │   └── webhooks.py              # LINE Webhook endpoint (/webhook/line)
│   ├── handlers/
│   │   ├── index_handler.py         # Handle "美股" query
│   │   ├── stock_handler.py         # Handle "AAPL" query
│   │   ├── news_handler.py          # Handle "新聞" query
│   │   └── tw_stock_handler.py      # Handle "台股 AAPL" query
│   ├── services/
│   │   ├── market_data.py           # Fetch index/stock data
│   │   ├── news_service.py          # Fetch & summarize news
│   │   └── tw_stock_service.py      # Taiwan correlation lookup
│   ├── models/
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── domain.py                # Domain entities
│   │   └── database.py              # SQLAlchemy ORM models
│   ├── integrations/
│   │   ├── yahoo_finance.py         # Yahoo Finance API wrapper
│   │   ├── alpha_vantage.py         # Alpha Vantage API wrapper
│   │   ├── google_news.py           # Google News RSS client
│   │   └── line_api.py              # LINE Messaging API wrapper
│   ├── utils/
│   │   ├── validators.py            # Input validation (stock codes, etc.)
│   │   ├── formatters.py            # Message formatting (zh-TW)
│   │   ├── logger.py                # Structured logging
│   │   ├── retry.py                 # Retry logic
│   │   └── errors.py                # Custom exceptions
│   ├── db/
│   │   ├── database.py              # Database connection & sessions
│   │   └── repositories.py          # Data access layer
│   └── exceptions.py                # Global exception definitions
├── tests/
│   ├── unit/                        # Unit tests
│   │   ├── test_validators.py
│   │   ├── test_formatters.py
│   │   └── test_handlers.py
│   ├── integration/                 # Integration tests
│   │   ├── test_webhook_routes.py
│   │   └── test_api_integrations.py
│   ├── fixtures/
│   │   └── mock_api_responses.py
│   └── conftest.py                  # pytest configuration
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata
├── Dockerfile                       # Docker image definition
├── docker-compose.yml               # Docker Compose for local dev
├── .env.example                     # Environment variables template
├── README.md                        # Project documentation (zh-TW)
├── ARCHITECTURE.md                  # Technical architecture
└── DEPLOYMENT.md                    # Deployment instructions

```

### Key Directory Functions

| Directory | Purpose |
|-----------|---------|
| `src/` | Source code (all application logic) |
| `src/api/` | HTTP endpoints (Webhook routes) |
| `src/handlers/` | Business logic handlers (query parsing, response building) |
| `src/services/` | External API integration (market data, news, etc.) |
| `src/models/` | Data models (Pydantic schemas, SQLAlchemy ORM) |
| `src/utils/` | Utility functions (validation, formatting, logging) |
| `tests/` | Test suites (unit + integration tests) |

---

## Running the Bot

### Start the Development Server

```bash
# From project root, with venv activated
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Access Swagger API Documentation

Open your browser and visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

You'll see:
- All available endpoints
- Request/response schemas
- Interactive API tester

### Test Webhook Endpoint

```bash
# Manual webhook test (replace with actual LINE event)
curl -X POST http://127.0.0.1:8000/webhook/line \
  -H "Content-Type: application/json" \
  -H "X-Line-Signature: <valid-signature>" \
  -d '{
    "events": [
      {
        "type": "message",
        "message": {"type": "text", "text": "美股"},
        "replyToken": "nHuyWiB7yP5Zw52FIkcQT",
        "timestamp": 1620000000000,
        "source": {"type": "user", "userId": "U4af4980482..."}
      }
    ],
    "destination": "xxxxxxxxxx"
  }'
```

---

## Testing & Validation

### Run Unit Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_validators.py -v

# Run with detailed output
pytest tests/ -vv --tb=short
```

### Expected Test Output

```
tests/unit/test_validators.py::test_validate_stock_code_valid PASSED
tests/unit/test_validators.py::test_validate_stock_code_invalid PASSED
tests/unit/test_formatters.py::test_format_index_message PASSED
...
========================= 45 passed in 3.21s =========================
```

### Code Quality Checks

```bash
# Format code with Black
black src/ tests/

# Check PEP 8 style (optional)
flake8 src/ tests/ --max-line-length=120

# Type checking with mypy (optional)
mypy src/ --strict
```

---

## Webhook Configuration

### 1. Set Up LINE Webhook URL

1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Select your Channel
3. Navigate to: **Messaging API** → **Webhook**
4. Set **Webhook URL** to: `https://your-domain.com/webhook/line`
5. Click **Verify** to test the connection
6. Enable **Use Webhook**

### 2. Test Webhook Locally (Using ngrok)

For local development, expose your local server to the internet:

```bash
# Install ngrok (if not already installed)
# Visit: https://ngrok.com/download

# Run ngrok to tunnel localhost:8000
ngrok http 8000
```

**Output**:
```
Session Status                online
Session Expires               2 hours, 58 minutes
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

3. Use the forwarding URL in LINE Developers Console:
   - Webhook URL: `https://abc123.ngrok.io/webhook/line`

### 3. Signature Verification

The webhook middleware automatically verifies HMAC-SHA256 signatures:

```python
# In src/api/webhooks.py
@app.post("/webhook/line")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # Verify signature (HMAC-SHA256)
    if not verify_signature(body, signature, CHANNEL_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process events...
```

---

## Debugging & Troubleshooting

### Common Issues

#### Issue 1: "Invalid Signature" Error

**Cause**: Webhook signature verification failed

**Solution**:
1. Verify `LINE_CHANNEL_SECRET` in `.env` is correct
2. Check LINE Developers Console for correct secret value
3. Ensure request body is not modified before signature verification

#### Issue 2: "API Timeout" Error

**Cause**: External API (Yahoo Finance, etc.) taking too long

**Solution**:
1. Check internet connection
2. Try with backup API (Alpha Vantage)
3. Increase timeout in `src/config.py` (default: 20s)

```python
# In src/config.py
API_TIMEOUT = 20  # Seconds
```

#### Issue 3: Stock Code Not Found

**Cause**: Invalid stock code or data source issue

**Solution**:
1. Verify stock code format (1-5 uppercase letters)
2. Check if Yahoo Finance is responding:
   ```bash
   python -c "import yfinance as yf; print(yf.Ticker('AAPL').info)"
   ```
3. Check database corruption:
   ```bash
   python -m src.db.database reset
   ```

### Enable Debug Logging

Add to `.env`:
```
DEBUG=true
LOG_LEVEL=DEBUG
```

View logs:
```bash
# Check application logs
tail -f logs/app.log

# Check Webhook requests
tail -f logs/webhook.log
```

---

## Deployment

### Option 1: Docker (Recommended)

```bash
# Build Docker image
docker build -t linebot-us-stock:latest .

# Run container
docker run -p 8000:8000 \
  -e LINE_CHANNEL_ACCESS_TOKEN=your_token \
  -e LINE_CHANNEL_SECRET=your_secret \
  -e DATABASE_URL=postgresql://user:pass@localhost/db \
  linebot-us-stock:latest
```

### Option 2: Linux Server (Ubuntu 20.04+)

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv postgresql

# Clone repository
git clone https://github.com/yourusername/linebot-us-stock.git
cd linebot-us-stock

# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure systemd service
sudo cp deploy/linebot-us-stock.service /etc/systemd/system/
sudo systemctl enable linebot-us-stock
sudo systemctl start linebot-us-stock
```

### Option 3: Cloud Platforms

- **Heroku**: See `Procfile` for deployment
- **AWS Lambda**: See `DEPLOYMENT.md`
- **Google Cloud Run**: See `DEPLOYMENT.md`

---

## Next Steps

1. ✅ Set up local development environment
2. ✅ Run tests and verify everything works
3. ✅ Configure LINE Webhook
4. ✅ Test with LINE Bot (via ngrok)
5. 📋 Read [ARCHITECTURE.md](../ARCHITECTURE.md) for technical details
6. 📋 Read [DEPLOYMENT.md](../DEPLOYMENT.md) for production deployment

---

## Support & Resources

- **LINE Developers**: https://developers.line.biz/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **LINE Bot SDK (Python)**: https://github.com/line/line-bot-sdk-python
- **yfinance Documentation**: https://yfinance.readthedocs.io/

---

**Quick Start Status**: ✅ COMPLETE  
**Last Updated**: 2026-05-17
