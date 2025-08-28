"""
Risk assessment routes for hazard predictions.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import redis.asyncio as redis

from app.config import settings
from app.db.models import HazardPrediction, User
from app.db.database import get_db
from app.geo.grid import grid_system
from app.routes.auth import get_current_active_user
from app.utils.sanitize import sanitize_text

router = APIRouter()

# Redis client for caching
redis_client = redis.from_url(settings.redis_url)


class RiskQuery(BaseModel):
    """Risk query model."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    hazards: Optional[List[str]] = Field(
        default=["flood", "heat", "smoke", "pm25"],
        description="Hazard types to query"
    )
    horizon_hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=72,
        description="Prediction horizon in hours"
    )


class RiskPrediction(BaseModel):
    """Risk prediction model."""
    hazard: str
    p_risk: float
    q10: Optional[float] = None
    q50: Optional[float] = None
    q90: Optional[float] = None
    model: str
    updated_at: str


class RiskResponse(BaseModel):
    """Risk response model."""
    grid_id: str
    horizon: int
    predictions: List[RiskPrediction]
    top_drivers: List[Dict[str, Any]]
    brief: Optional[str] = None
    sources: Optional[List[str]] = None


@router.post("/query", response_model=RiskResponse)
async def query_risk(
    query: RiskQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Query risk predictions for a location.
    
    Args:
        query: Risk query parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Risk predictions and analysis
    """
    # Sanitize inputs
    lat = query.lat
    lon = query.lon
    hazards = [sanitize_text(h) for h in query.hazards]
    horizon_hours = query.horizon_hours
    
    # Get grid ID for location
    grid_id = grid_system.point_to_grid_id(lat, lon)
    
    # Check cache first
    cache_key = f"risk:{grid_id}:{':'.join(hazards)}:{horizon_hours}"
    cached_result = await redis_client.get(cache_key)
    
    if cached_result and not settings.debug:
        import json
        return RiskResponse(**json.loads(cached_result))
    
    # Query database for recent predictions
    horizon_minutes = horizon_hours * 60
    
    predictions = []
    for hazard in hazards:
        if hazard not in ["flood", "heat", "smoke", "pm25"]:
            continue
            
        result = await db.execute(
            select(HazardPrediction)
            .where(
                and_(
                    HazardPrediction.type == hazard,
                    HazardPrediction.grid_id == grid_id,
                    HazardPrediction.horizon_minutes <= horizon_minutes
                )
            )
            .order_by(desc(HazardPrediction.issued_at))
            .limit(1)
        )
        
        hazard_pred = result.scalar_one_or_none()
        
        if hazard_pred:
            predictions.append(RiskPrediction(
                hazard=hazard,
                p_risk=hazard_pred.p_risk,
                q10=hazard_pred.q10,
                q50=hazard_pred.q50,
                q90=hazard_pred.q90,
                model=hazard_pred.model_version,
                updated_at=hazard_pred.issued_at.isoformat()
            ))
        elif settings.demo_mode:
            # Generate demo data
            import random
            predictions.append(RiskPrediction(
                hazard=hazard,
                p_risk=random.uniform(0.1, 0.8),
                q10=random.uniform(0.05, 0.3),
                q50=random.uniform(0.2, 0.6),
                q90=random.uniform(0.4, 0.9),
                model="demo-model-v1",
                updated_at="2024-01-01T00:00:00Z"
            ))
    
    # Generate top drivers (simplified for demo)
    top_drivers = [
        {"feature": "precipitation_24h", "contribution": 0.35},
        {"feature": "soil_moisture", "contribution": 0.28},
        {"feature": "elevation", "contribution": 0.22},
        {"feature": "distance_to_water", "contribution": 0.15}
    ]
    
    # Generate brief (simplified for demo)
    brief = None
    if predictions:
        max_risk = max(p.p_risk for p in predictions)
        if max_risk > 0.5:
            brief = f"High risk conditions detected. Primary concern: {max(predictions, key=lambda x: x.p_risk).hazard} with {max_risk:.1%} probability. Monitor conditions closely."
        elif max_risk > 0.3:
            brief = f"Moderate risk conditions present. Main hazard: {max(predictions, key=lambda x: x.p_risk).hazard} with {max_risk:.1%} probability. Stay informed."
        else:
            brief = f"Low risk conditions. All hazards below 30% probability. Normal operations recommended."
    
    # Sources
    sources = ["NOAA", "USGS", "EPA AirNow", "NASA FIRMS"]
    
    response = RiskResponse(
        grid_id=grid_id,
        horizon=horizon_hours,
        predictions=predictions,
        top_drivers=top_drivers,
        brief=brief,
        sources=sources
    )
    
    # Cache result
    if not settings.debug:
        import json
        await redis_client.setex(
            cache_key,
            settings.prediction_cache_ttl_seconds,
            json.dumps(response.dict(), ensure_ascii=True)
        )
    
    return response


@router.get("/geocode")
async def geocode(
    query: str = Query(..., description="Address or location to geocode"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Geocode address to lat/lon coordinates.
    
    Args:
        query: Address or location string
        current_user: Current authenticated user
        
    Returns:
        Geocoded coordinates and administrative areas
    """
    # Sanitize query
    query = sanitize_text(query)
    
    # Check cache
    cache_key = f"geocode:{query}"
    cached_result = await redis_client.get(cache_key)
    
    if cached_result and not settings.debug:
        import json
        return json.loads(cached_result)
    
    # Simplified geocoding for demo
    # In production, use a proper geocoding service
    demo_locations = {
        "san francisco": {"lat": 37.7749, "lon": -122.4194, "admin_areas": ["California", "San Francisco County"]},
        "new york": {"lat": 40.7128, "lon": -74.0060, "admin_areas": ["New York", "New York County"]},
        "chicago": {"lat": 41.8781, "lon": -87.6298, "admin_areas": ["Illinois", "Cook County"]},
        "miami": {"lat": 25.7617, "lon": -80.1918, "admin_areas": ["Florida", "Miami-Dade County"]},
        "seattle": {"lat": 47.6062, "lon": -122.3321, "admin_areas": ["Washington", "King County"]},
    }
    
    query_lower = query.lower()
    result = None
    
    for location, coords in demo_locations.items():
        if location in query_lower:
            result = {
                "point": {"lat": coords["lat"], "lon": coords["lon"]},
                "admin_areas": coords["admin_areas"]
            }
            break
    
    if not result:
        # Default to San Francisco for demo
        result = {
            "point": {"lat": 37.7749, "lon": -122.4194},
            "admin_areas": ["California", "San Francisco County"]
        }
    
    # Cache result
    if not settings.debug:
        import json
        await redis_client.setex(
            cache_key,
            3600,  # 1 hour cache
            json.dumps(result, ensure_ascii=True)
        )
    
    return result
