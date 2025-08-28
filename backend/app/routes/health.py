"""
Health check routes for monitoring and observability.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
from datetime import datetime

from app.config import settings
from app.db.database import get_db

router = APIRouter()

# Redis client for health checks
redis_client = redis.from_url(settings.redis_url)


@router.get("/healthz")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@router.get("/readyz")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check endpoint.
    
    Args:
        db: Database session
        
    Returns:
        Readiness status
    """
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Check Redis connection
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    overall_status = "ready" if db_status == "healthy" and redis_status == "healthy" else "not_ready"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_status,
            "redis": redis_status
        }
    }
