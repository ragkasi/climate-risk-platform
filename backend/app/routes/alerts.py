"""
Alert management routes for notifications and subscriptions.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.config import settings
from app.db.models import Alert, Site, Organization, User
from app.db.database import get_db
from app.routes.auth import get_current_active_user
from app.utils.sanitize import sanitize_text

router = APIRouter()


class AlertSubscription(BaseModel):
    """Alert subscription model."""
    site_ids: List[str]
    hazard: str
    threshold: float
    channel: List[str]  # email, webhook
    webhook_url: Optional[str] = None


class AlertSubscriptionResponse(BaseModel):
    """Alert subscription response model."""
    subscription_id: str


@router.post("/subscribe", response_model=AlertSubscriptionResponse)
async def subscribe_alerts(
    subscription: AlertSubscription,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Subscribe to alerts for specific sites and hazards.
    
    Args:
        subscription: Alert subscription details
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Subscription ID
    """
    if not current_user.org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Validate sites belong to user's organization
    for site_id in subscription.site_ids:
        result = await db.execute(
            select(Site).where(
                Site.id == site_id,
                Site.org_id == current_user.org_id
            )
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    
    # Validate hazard type
    if subscription.hazard not in ["flood", "heat", "smoke", "pm25"]:
        raise HTTPException(status_code=400, detail="Invalid hazard type")
    
    # Validate threshold
    if not 0.0 <= subscription.threshold <= 1.0:
        raise HTTPException(status_code=400, detail="Threshold must be between 0.0 and 1.0")
    
    # Validate channels
    valid_channels = ["email", "webhook"]
    for channel in subscription.channel:
        if channel not in valid_channels:
            raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
    
    # Create alert subscriptions
    subscription_id = str(uuid.uuid4())
    
    for site_id in subscription.site_ids:
        for channel in subscription.channel:
            alert = Alert(
                org_id=current_user.org_id,
                site_id=site_id,
                hazard_type=subscription.hazard,
                p_risk=0.0,  # Will be updated when risk is calculated
                threshold=subscription.threshold,
                channel=channel,
                webhook_url=sanitize_text(subscription.webhook_url) if subscription.webhook_url else None,
                status="pending"
            )
            db.add(alert)
    
    await db.commit()
    
    return AlertSubscriptionResponse(subscription_id=subscription_id)


@router.get("/")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List alerts for the current user's organization.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of alerts
    """
    if not current_user.org_id:
        return []
    
    result = await db.execute(
        select(Alert).where(Alert.org_id == current_user.org_id)
    )
    alerts = result.scalars().all()
    
    return [
        {
            "id": str(alert.id),
            "site_id": str(alert.site_id) if alert.site_id else None,
            "hazard_type": alert.hazard_type,
            "status": alert.status,
            "p_risk": alert.p_risk,
            "threshold": alert.threshold,
            "channel": alert.channel,
            "sent_at": alert.sent_at.isoformat() if alert.sent_at else None,
            "created_at": alert.created_at.isoformat()
        }
        for alert in alerts
    ]
