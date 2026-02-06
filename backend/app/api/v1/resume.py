"""
Resume API endpoints.
Handles resume upload, processing, and management.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.core import security
from app.db.session import get_db
from app.models.resume import Resume
from app.models.user import User
from app.agents.resume_agent import ResumeAgent
from app.utils.file_handler import get_file_size, is_valid_file_type

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload", response_model=dict)
async def upload_resume(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Upload and process a resume file.
    """
    # Validate file type
    if not is_valid_file_type(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    file_content = await file.read()

    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )

    # Process resume
    resume_agent = ResumeAgent()
    result = resume_agent.process_resume_upload(
        user_id=current_user.id,
        file_content=file_content,
        filename=file.filename,
        db=db
    )

    if result["status"] != "success":
        raise HTTPException(status_code=500, detail="Failed to process resume")

    return result

@router.get("/", response_model=List[dict])
def read_resumes(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Retrieve user's resumes.
    """
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": resume.id,
            "filename": resume.filename,
            "skills": resume.skills.split(",") if resume.skills else [],
            "experience_years": resume.experience_years,
            "education_level": resume.education_level,
            "created_at": resume.created_at,
        }
        for resume in resumes
    ]

@router.get("/{resume_id}", response_model=dict)
def read_resume(
    *,
    db: Session = Depends(get_db),
    resume_id: int,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Get a specific resume by ID.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_agent = ResumeAgent()
    analysis = resume_agent.get_resume_analysis(resume_id, db)

    if not analysis:
        raise HTTPException(status_code=404, detail="Resume analysis not found")

    return analysis

@router.delete("/{resume_id}")
def delete_resume(
    *,
    db: Session = Depends(get_db),
    resume_id: int,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Delete a resume.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Delete file from disk
    import os
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)

    # Delete from database
    db.delete(resume)
    db.commit()

    return {"message": "Resume deleted successfully"}
