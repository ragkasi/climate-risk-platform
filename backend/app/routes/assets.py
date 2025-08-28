"""
Asset management routes for site uploads and risk queries.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import csv
import json
import uuid

from app.config import settings
from app.db.models import Site, Organization, User
from app.db.database import get_db
from app.routes.auth import get_current_active_user
from app.utils.sanitize import sanitize_text

router = APIRouter()


class SiteRiskResponse(BaseModel):
    """Site risk response model."""
    site_id: str
    time: str
    hazard: str
    p_risk: float
    q10: Optional[float] = None
    q50: Optional[float] = None
    q90: Optional[float] = None
    brief: Optional[str] = None


@router.post("/upload")
async def upload_assets(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload CSV or GeoJSON file with asset locations.
    
    Args:
        file: Uploaded file
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Upload results with site IDs
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Get user's organization
    if not current_user.org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    content = await file.read()
    site_ids = []
    
    try:
        if file.filename.endswith('.csv'):
            # Parse CSV
            csv_content = content.decode('utf-8')
            reader = csv.DictReader(csv_content.splitlines())
            
            for row in reader:
                name = sanitize_text(row.get('name', f'Site {len(site_ids) + 1}'))
                lat = float(row.get('lat', 0))
                lon = float(row.get('lon', 0))
                
                # Create site
                site = Site(
                    org_id=current_user.org_id,
                    name=name,
                    geom=f"POINT({lon} {lat})",
                    metadata={"source": "csv_upload"}
                )
                db.add(site)
                await db.flush()
                site_ids.append(str(site.id))
        
        elif file.filename.endswith('.geojson'):
            # Parse GeoJSON
            geojson_data = json.loads(content.decode('utf-8'))
            
            for feature in geojson_data.get('features', []):
                name = sanitize_text(feature.get('properties', {}).get('name', f'Site {len(site_ids) + 1}'))
                coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                lon, lat = coords[0], coords[1]
                
                # Create site
                site = Site(
                    org_id=current_user.org_id,
                    name=name,
                    geom=f"POINT({lon} {lat})",
                    metadata={"source": "geojson_upload"}
                )
                db.add(site)
                await db.flush()
                site_ids.append(str(site.id))
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        await db.commit()
        
        return {
            "site_ids": site_ids,
            "stats": {
                "total_sites": len(site_ids),
                "file_type": file.filename.split('.')[-1]
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")


@router.get("/{site_id}/risk")
async def get_site_risk(
    site_id: str,
    horizon_hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get risk predictions for a specific site.
    
    Args:
        site_id: Site ID
        horizon_hours: Prediction horizon in hours
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Risk predictions for the site
    """
    # Get site
    result = await db.execute(
        select(Site).where(
            Site.id == site_id,
            Site.org_id == current_user.org_id
        )
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # In a real implementation, this would query the hazard predictions
    # For demo, return mock data
    if settings.demo_mode:
        import random
        from datetime import datetime, timedelta
        
        predictions = []
        hazards = ["flood", "heat", "smoke", "pm25"]
        
        for hazard in hazards:
            predictions.append(SiteRiskResponse(
                site_id=site_id,
                time=(datetime.utcnow() + timedelta(hours=horizon_hours)).isoformat(),
                hazard=hazard,
                p_risk=random.uniform(0.1, 0.8),
                q10=random.uniform(0.05, 0.3),
                q50=random.uniform(0.2, 0.6),
                q90=random.uniform(0.4, 0.9),
                brief=f"Demo risk assessment for {hazard} at {site.name}"
            ))
        
        return predictions
    
    return []
