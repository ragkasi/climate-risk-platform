"""
Admin routes for system management and monitoring.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import redis.asyncio as redis

from app.config import settings
from app.db.models import User, HazardPrediction, Alert, Telemetry
from app.db.database import get_db
from app.routes.auth import get_current_active_user

router = APIRouter()

# Redis client for metrics
redis_client = redis.from_url(settings.redis_url)


class ExperimentConfig(BaseModel):
    """Experiment configuration model."""
    variant_config: Dict[str, Any]


@router.post("/reindex_tiles")
async def reindex_tiles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reindex map tiles.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Check admin permissions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, this would trigger tile rebuilding
    # For demo, just return success
    return {"message": "Tile reindexing started", "status": "success"}


@router.post("/retrain")
async def retrain_models(
    hazard: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrain ML models.
    
    Args:
        hazard: Specific hazard to retrain (optional)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Check admin permissions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, this would trigger model retraining
    # For demo, just return success
    return {
        "message": f"Model retraining started for {hazard or 'all hazards'}",
        "status": "success"
    }


@router.get("/metrics")
async def get_admin_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get system metrics for monitoring.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        System metrics
    """
    # Check admin permissions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get database metrics
    hazard_count = await db.execute(select(func.count(HazardPrediction.hazard_id)))
    alert_count = await db.execute(select(func.count(Alert.id)))
    telemetry_count = await db.execute(select(func.count(Telemetry.id)))
    
    # Get Redis metrics
    try:
        redis_info = await redis_client.info()
        redis_memory = redis_info.get('used_memory_human', 'Unknown')
        redis_connected_clients = redis_info.get('connected_clients', 0)
    except Exception:
        redis_memory = "Unknown"
        redis_connected_clients = 0
    
    # Mock latency metrics for demo
    latency_metrics = {
        "data_latency_p50_ms": 150,
        "data_latency_p95_ms": 500,
        "prediction_latency_p50_ms": 200,
        "prediction_latency_p95_ms": 800,
        "tile_build_duration_ms": 1200
    }
    
    # Mock cache metrics
    cache_metrics = {
        "cache_hit_ratio": 0.85,
        "tile_cache_hit_ratio": 0.92,
        "prediction_cache_hit_ratio": 0.78
    }
    
    # Mock queue metrics
    queue_metrics = {
        "celery_queue_depth": 5,
        "data_ingestion_queue": 2,
        "alert_queue": 0
    }
    
    return {
        "database": {
            "hazard_predictions": hazard_count.scalar(),
            "alerts": alert_count.scalar(),
            "telemetry_records": telemetry_count.scalar()
        },
        "redis": {
            "memory_usage": redis_memory,
            "connected_clients": redis_connected_clients
        },
        "latency": latency_metrics,
        "cache": cache_metrics,
        "queue": queue_metrics,
        "data_freshness": {
            "last_weather_update": "2024-01-01T00:00:00Z",
            "last_air_quality_update": "2024-01-01T00:00:00Z",
            "last_hydrology_update": "2024-01-01T00:00:00Z"
        }
    }


@router.get("/experiments")
async def get_experiments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get A/B testing experiments.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of experiments
    """
    # Check admin permissions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Mock experiment data for demo
    experiments = [
        {
            "exp_id": "exp_001",
            "name": "Threshold Sensitivity",
            "variant": "A",
            "start_at": "2024-01-01T00:00:00Z",
            "stop_at": None,
            "is_active": True,
            "metrics": {
                "users_assigned": 150,
                "alerts_sent": 45,
                "false_positive_rate": 0.12,
                "user_satisfaction": 0.78
            }
        },
        {
            "exp_id": "exp_002", 
            "name": "Brief Length",
            "variant": "B",
            "start_at": "2024-01-01T00:00:00Z",
            "stop_at": None,
            "is_active": True,
            "metrics": {
                "users_assigned": 200,
                "alerts_sent": 60,
                "false_positive_rate": 0.08,
                "user_satisfaction": 0.85
            }
        }
    ]
    
    return experiments


@router.post("/experiments/start")
async def start_experiment(
    config: ExperimentConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Start a new A/B testing experiment.
    
    Args:
        config: Experiment configuration
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Check admin permissions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, this would create and start an experiment
    return {
        "message": "Experiment started successfully",
        "experiment_id": "exp_003",
        "status": "active"
    }


@router.post("/experiments/stop")
async def stop_experiment(
    exp_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Stop an A/B testing experiment.
    
    Args:
        exp_id: Experiment ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Check admin permissions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, this would stop the experiment
    return {
        "message": f"Experiment {exp_id} stopped successfully",
        "status": "stopped"
    }
