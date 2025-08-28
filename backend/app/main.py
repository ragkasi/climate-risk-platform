"""
FastAPI application factory with ASCII sanitization middleware.
"""

import json
from typing import Any, Dict
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.config import settings
from app.utils.sanitize import sanitize_dict
from app.routes import auth, risk, assets, alerts, admin, health, feedback


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Climate Risk Lens API",
        description="Geospatial platform for forecasting local climate hazards",
        version="0.1.0",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # ASCII sanitization middleware
    @app.middleware("http")
    async def sanitize_response_middleware(request: Request, call_next):
        response = await call_next(request)
        
        # Only sanitize JSON and text responses
        if (response.headers.get("content-type", "").startswith("application/json") or
            response.headers.get("content-type", "").startswith("text/")):
            
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                # Parse and sanitize JSON
                if response.headers.get("content-type", "").startswith("application/json"):
                    data = json.loads(body.decode())
                    sanitized_data = sanitize_dict(data)
                    sanitized_body = json.dumps(sanitized_data, ensure_ascii=True)
                else:
                    # Sanitize text content
                    from app.utils.sanitize import sanitize_text
                    sanitized_body = sanitize_text(body.decode())
                
                # Create new response with sanitized content
                return Response(
                    content=sanitized_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If parsing fails, return original response
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
        
        return response
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
    app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
    app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
    
    # Prometheus metrics
    if not settings.debug:
        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app, endpoint="/metrics")
    
    # OpenTelemetry instrumentation
    if not settings.debug:
        FastAPIInstrumentor.instrument_app(app)
    
    return app


# Create app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint with ASCII-only response."""
    return {
        "message": "Climate Risk Lens API",
        "version": "0.1.0",
        "status": "operational",
        "ascii_only": True
    }
