"""
Role API endpoints.
Handles role inference and recommendations.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core import security
from app.db.session import get_db
from app.models.user import User
from app.services.role_inference_service import RoleInferenceService
from app.models.resume import Resume

router = APIRouter()

@router.get("/recommendations/{resume_id}", response_model=dict)
def get_role_recommendations(
    *,
    db: Session = Depends(get_db),
    resume_id: int,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Get role recommendations for a specific resume.
    """
    # Verify resume ownership
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.content_text:
        raise HTTPException(status_code=400, detail="Resume content not available")

    # Generate role recommendations
    role_service = RoleInferenceService()
    recommendations = role_service.infer_roles(resume.content_text)

    return {
        "resume_id": resume_id,
        "recommendations": recommendations
    }

@router.post("/select/{resume_id}", response_model=dict)
def select_role(
    *,
    db: Session = Depends(get_db),
    resume_id: int,
    selected_role: str,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Select a role for job discovery and ATS scoring.
    """
    # Verify resume ownership
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Store selected role (you might want to add this to a model later)
    # For now, just return success with the selection

    return {
        "resume_id": resume_id,
        "selected_role": selected_role,
        "message": f"Role '{selected_role}' selected successfully. Ready for job discovery."
    }
