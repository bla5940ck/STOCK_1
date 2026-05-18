"""Minimal test app to verify Railway works"""
import os
import sys
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health():
    port = os.environ.get("PORT", "8000")
    return {
        "status": "ok",
        "port": port,
        "message": "Test app is running!"
    }

if __name__ == "__main__":
    # Read PORT from environment (Railway sets this automatically)
    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0"
    print(f"🚀 Starting server on {host}:{port}")
    print(f"📝 PORT env var: {os.environ.get('PORT', 'not set')}")
    uvicorn.run(app, host=host, port=port, log_level="info")
