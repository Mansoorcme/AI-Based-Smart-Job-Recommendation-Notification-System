"""
Job model for the application.
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import relationship # pyright: ignore[reportMissingImports]
from app.db.base import Base # pyright: ignore[reportMissingImports]

class Job(Base):
    """
    Job database model.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)  # ID from external API
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    salary_range = Column(String, nullable=True)
    job_type = Column(String, nullable=True)  # Full-time, Part-time, Contract, etc.
    posted_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    match_results = relationship("MatchResult", back_populates="job")
