#!/usr/bin/env python3
"""
Minimal Climate Risk Lens server without complex dependencies.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import json

app = FastAPI(
    title="Climate Risk Lens API",
    description="A production-grade geospatial platform for forecasting local climate hazards",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Climate Risk Lens API",
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "risk": "/api/v1/risk",
            "assets": "/api/v1/assets"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "services": {
            "api": "healthy",
            "database": "not_connected",
            "redis": "not_connected"
        }
    }

@app.get("/api/v1/risk")
async def get_risk_data():
    """Get climate risk data (demo endpoint)."""
    return {
        "message": "Climate risk data endpoint",
        "data": {
            "flood_risk": 0.3,
            "heat_risk": 0.4,
            "smoke_risk": 0.2,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@app.get("/api/v1/assets")
async def get_assets():
    """Get assets endpoint (demo)."""
    return {
        "message": "Assets endpoint",
        "assets": [
            {"id": 1, "name": "Demo Site 1", "risk_level": "medium"},
            {"id": 2, "name": "Demo Site 2", "risk_level": "low"}
        ]
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with ASCII sanitization."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("Starting Climate Risk Lens API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
