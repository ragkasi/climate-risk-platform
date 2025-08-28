#!/usr/bin/env python3
"""
Simple test to verify basic functionality.
"""

import asyncio
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Climate Risk Lens API is working!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Server is running"}

if __name__ == "__main__":
    print("Starting Climate Risk Lens API on http://localhost:8002")
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
