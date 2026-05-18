"""Minimal test app to verify Railway works"""
from fastapi import FastAPI
import os

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
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
