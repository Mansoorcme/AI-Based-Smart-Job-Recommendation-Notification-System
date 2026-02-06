"""
ATS matching agent.
Coordinates ATS scoring and matching operations.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.models.match_result import MatchResult
from app.models.resume import Resume
from app.models.job import Job
from app.services.ats_service import ATSService
from app.services.llm_explain_service import LLMExplainService
from app.services.notification_service import NotificationService

class ATSAgent:
    """
    Agent for handling ATS matching operations.
    """

    def __init__(self):
        self.ats_service = ATSService()
        self.llm_service = LLMExplainService()

    def calculate_match(
        self,
        resume_id: int,
        job_id: int,
        user_id: int,
        db: Session
    ) -> Optional[Dict[str, any]]:
        """
        Calculate ATS match between resume and job.

        Args:
            resume_id: Resume ID
            job_id: Job ID
            user_id: User ID
            db: Database session

        Returns:
            Match result data
        """
        try:
            # Get resume and job data
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            job = db.query(Job).filter(Job.id == job_id).first()

            if not resume or not job:
                logger.error(f"Resume {resume_id} or job {job_id} not found")
                return None

            # Calculate ATS score
            match_data = self.ats_service.calculate_match_score(
                resume.content_text or "",
                job.description,
                job.requirements or "",
                resume.skills.split(",") if resume.skills else []
            )

            # Generate LLM explanations
            explanation = self.llm_service.generate_match_explanation(
                resume.content_text or "",
                job.description,
                job.requirements or "",
                match_data["ats_score"],
                match_data
            )

            missing_skills = self.llm_service.identify_missing_skills(
                resume.skills.split(",") if resume.skills else [],
                job.description,
                job.requirements or ""
            )

            improvements = self.llm_service.generate_resume_improvements(
                resume.content_text or "",
                job.description,
                job.requirements or "",
                missing_skills
            )

            # Store match result
            match_result = MatchResult(
                user_id=user_id,
                resume_id=resume_id,
                job_id=job_id,
                ats_score=match_data["ats_score"],
                skill_match_score=match_data["skill_match_score"],
                role_similarity_score=match_data["role_similarity_score"],
                keyword_overlap_score=match_data["keyword_overlap_score"],
                experience_match_score=match_data["experience_match_score"],
                explanation=explanation,
                missing_skills=",".join(missing_skills),
                resume_improvements=improvements
            )

            db.add(match_result)
            db.commit()
            db.refresh(match_result)

            # Send notification for high-scoring matches
            if match_data["ats_score"] >= 80:
                notification_service = NotificationService()
                notification_service.send_job_match_notification(
                    user_id=user_id,
                    job_title=job.title,
                    company=job.company,
                    match_score=match_data["ats_score"]
                )

            logger.info(f"Calculated match for user {user_id}: {match_data['ats_score']:.1f}%")

            return {
                "match_id": match_result.id,
                "ats_score": match_result.ats_score,
                "component_scores": {
                    "skill_match": match_result.skill_match_score,
                    "role_similarity": match_result.role_similarity_score,
                    "keyword_overlap": match_result.keyword_overlap_score,
                    "experience_match": match_result.experience_match_score
                },
                "explanation": explanation,
                "missing_skills": missing_skills,
                "resume_improvements": improvements
            }

        except Exception as e:
            logger.error(f"Error calculating match for user {user_id}: {e}")
            db.rollback()
            return None

    def get_match_history(
        self,
        user_id: int,
        db: Session,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """
        Get user's match history.

        Args:
            user_id: User ID
            db: Database session
            limit: Maximum results

        Returns:
            List of match results
        """
        try:
            matches = (
                db.query(MatchResult)
                .filter(MatchResult.user_id == user_id)
                .order_by(MatchResult.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "match_id": match.id,
                    "job_title": match.job.title,
                    "company": match.job.company,
                    "ats_score": match.ats_score,
                    "created_at": match.created_at
                }
                for match in matches
            ]

        except Exception as e:
            logger.error(f"Error getting match history for user {user_id}: {e}")
            return []
