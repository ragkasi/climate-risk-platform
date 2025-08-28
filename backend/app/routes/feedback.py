"""
Feedback routes for model improvement.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.db.models import Feedback, HazardPrediction, User
from app.db.database import get_db
from app.routes.auth import get_current_active_user
from app.utils.sanitize import sanitize_text

router = APIRouter()


class FeedbackSubmission(BaseModel):
    """Feedback submission model."""
    hazard_id: str
    label: str  # TP, FP, FN, TN
    notes: Optional[str] = None


@router.post("/")
async def submit_feedback(
    feedback: FeedbackSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit feedback on hazard predictions.
    
    Args:
        feedback: Feedback data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    if not settings.enable_feedback:
        raise HTTPException(status_code=400, detail="Feedback is disabled")
    
    # Validate label
    valid_labels = ["TP", "FP", "FN", "TN"]
    if feedback.label not in valid_labels:
        raise HTTPException(status_code=400, detail="Invalid label. Must be TP, FP, FN, or TN")
    
    # Verify hazard prediction exists
    result = await db.execute(
        select(HazardPrediction).where(HazardPrediction.hazard_id == feedback.hazard_id)
    )
    hazard_pred = result.scalar_one_or_none()
    
    if not hazard_pred:
        raise HTTPException(status_code=404, detail="Hazard prediction not found")
    
    # Create feedback record
    feedback_record = Feedback(
        hazard_id=feedback.hazard_id,
        user_id=current_user.id,
        label=feedback.label,
        notes=sanitize_text(feedback.notes) if feedback.notes else None
    )
    
    db.add(feedback_record)
    await db.commit()
    
    return {
        "message": "Feedback submitted successfully",
        "feedback_id": str(feedback_record.id)
    }


@router.get("/")
async def get_feedback(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get feedback records for the current user.
    
    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of feedback records
    """
    if not settings.enable_feedback:
        return []
    
    result = await db.execute(
        select(Feedback)
        .where(Feedback.user_id == current_user.id)
        .limit(limit)
        .offset(offset)
    )
    feedback_records = result.scalars().all()
    
    return [
        {
            "id": str(feedback.id),
            "hazard_id": str(feedback.hazard_id),
            "label": feedback.label,
            "notes": feedback.notes,
            "created_at": feedback.created_at.isoformat()
        }
        for feedback in feedback_records
    ]
