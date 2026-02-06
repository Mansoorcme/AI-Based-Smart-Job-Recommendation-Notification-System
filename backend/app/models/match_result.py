"""
Match result model for ATS scoring.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class MatchResult(Base):
    """
    Match result database model.
    """
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    ats_score = Column(Float, nullable=False)  # Overall ATS match percentage (0-100)
    skill_match_score = Column(Float, nullable=False)  # 40% weight
    role_similarity_score = Column(Float, nullable=False)  # 25% weight
    keyword_overlap_score = Column(Float, nullable=False)  # 20% weight
    experience_match_score = Column(Float, nullable=False)  # 15% weight
    explanation = Column(Text, nullable=True)  # LLM-generated explanation
    missing_skills = Column(Text, nullable=True)  # JSON string of missing skills
    resume_improvements = Column(Text, nullable=True)  # LLM-generated suggestions
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="match_results")
    resume = relationship("Resume", back_populates="match_results")
    job = relationship("Job", back_populates="match_results")
