#!/usr/bin/env python
"""
Startup script that reads PORT env var and launches uvicorn.
"""
import os
import sys
import subprocess

port = os.environ.get("PORT", "8000")
print(f"Starting uvicorn on port {port}")

cmd = [
    sys.executable, "-m", "uvicorn",
    "src.main:app",
    "--host", "0.0.0.0",
    "--port", port
]

subprocess.run(cmd)
