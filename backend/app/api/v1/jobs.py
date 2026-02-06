"""
Jobs API endpoints.
Handles job fetching, searching, and management.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core import security
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobInDB, JobSearch
from app.services.job_fetch_service import JobFetchService

router = APIRouter()

@router.get("/search", response_model=List[JobInDB])
def search_jobs(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., description="Search query for jobs"),
    location: str = Query(None, description="Job location"),
    limit: int = Query(20, description="Number of jobs to return"),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Search for jobs based on query and location.
    """
    job_service = JobFetchService()
    jobs_data = job_service.search_jobs(q, location, limit)

    # Save jobs to database if not exists
    jobs = []
    for job_data in jobs_data:
        job = db.query(Job).filter(Job.external_id == job_data["id"]).first()
        if not job:
            job = Job(
                external_id=job_data["id"],
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                description=job_data["description"],
                requirements=job_data.get("requirements", ""),
                salary_range=job_data.get("salary_range"),
                job_type=job_data.get("job_type"),
                posted_date=job_data.get("posted_date"),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
        jobs.append(job)

    return jobs

@router.get("/{job_id}", response_model=JobInDB)
def read_job(
    *,
    db: Session = Depends(get_db),
    job_id: int,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Get a specific job by ID.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/", response_model=List[JobInDB])
def read_jobs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Retrieve all jobs.
    """
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs
