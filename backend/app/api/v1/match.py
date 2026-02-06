"""
Match API endpoints.
Handles ATS matching between resumes and jobs.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core import security
from app.db.session import get_db
from app.models.user import User
from app.agents.ats_agent import ATSAgent
from app.utils.validators import MatchRequest

router = APIRouter()

@router.post("/", response_model=dict)
def create_match(
    *,
    db: Session = Depends(get_db),
    match_request: MatchRequest,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Calculate ATS match between a resume and job.
    """
    ats_agent = ATSAgent()
    result = ats_agent.calculate_match(
        resume_id=match_request.resume_id,
        job_id=match_request.job_id,
        user_id=current_user.id,
        db=db
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Unable to calculate match")
    
    return result

@router.get("/history", response_model=list)
def get_match_history(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Get user's match history.
    """
    ats_agent = ATSAgent()
    history = ats_agent.get_match_history(current_user.id, db, limit)
    
    return history

@router.get("/{match_id}", response_model=dict)
def get_match_details(
    *,
    db: Session = Depends(get_db),
    match_id: int,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Get detailed information about a specific match.
    """
    from app.models.match_result import MatchResult
    
    match = db.query(MatchResult).filter(
        MatchResult.id == match_id,
        MatchResult.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    return {
        "match_id": match.id,
        "ats_score": match.ats_score,
        "component_scores": {
            "skill_match": match.skill_match_score,
            "role_similarity": match.role_similarity_score,
            "keyword_overlap": match.keyword_overlap_score,
            "experience_match": match.experience_match_score,
        },
        "explanation": match.explanation,
        "missing_skills": match.missing_skills.split(",") if match.missing_skills else [],
        "resume_improvements": match.resume_improvements,
        "job": {
            "title": match.job.title,
            "company": match.job.company,
            "location": match.job.location,
        },
        "created_at": match.created_at,
    }
