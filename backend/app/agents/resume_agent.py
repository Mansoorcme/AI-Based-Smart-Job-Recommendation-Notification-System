"""
Resume processing agent.
Coordinates resume upload, parsing, and analysis.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.models.resume import Resume
from app.services.resume_service import ResumeService
from app.services.llm_explain_service import LLMExplainService
from app.services.role_inference_service import RoleInferenceService

class ResumeAgent:
    """
    Agent for handling resume-related operations.
    """

    def __init__(self):
        self.resume_service = ResumeService()
        self.llm_service = LLMExplainService()

    def process_resume_upload(
        self,
        user_id: int,
        file_content: bytes,
        filename: str,
        db: Session
    ) -> Dict[str, any]:
        """
        Process resume upload: save file, extract text, parse skills.

        Args:
            user_id: User ID
            file_content: Resume file content
            filename: Original filename
            db: Database session

        Returns:
            Dictionary with processing results
        """
        try:
            # Save file and extract text
            file_path = self.resume_service.save_resume_file(file_content, filename, user_id)
            extracted_text = self.resume_service.extract_text_from_file(file_path)

            # Parse resume content
            parsed_data = self.resume_service.parse_resume_content(extracted_text)

            # Create resume record
            resume = Resume(
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                content_text=extracted_text,
                skills=",".join(parsed_data.get("skills", [])),
                experience_years=parsed_data.get("experience_years"),
                education_level=parsed_data.get("education_level")
            )

            db.add(resume)
            db.commit()
            db.refresh(resume)

            logger.info(f"Resume processed for user {user_id}: {filename}")

            # Generate role recommendations using LLM
            role_recommendations = self.role_inference_service.infer_roles(extracted_text)

            return {
                "resume_id": resume.id,
                "filename": filename,
                "skills": parsed_data.get("skills", []),
                "experience_years": parsed_data.get("experience_years"),
                "education_level": parsed_data.get("education_level"),
                "role_recommendations": role_recommendations,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error processing resume for user {user_id}: {e}")
            db.rollback()
            raise

    def get_resume_analysis(self, resume_id: int, db: Session) -> Optional[Dict[str, any]]:
        """
        Get detailed analysis of a resume.

        Args:
            resume_id: Resume ID
            db: Database session

        Returns:
            Resume analysis data
        """
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return None

        skills = resume.skills.split(",") if resume.skills else []

        return {
            "resume_id": resume.id,
            "filename": resume.filename,
            "skills": skills,
            "experience_years": resume.experience_years,
            "education_level": resume.education_level,
            "content_preview": resume.content_text[:500] if resume.content_text else "",
            "created_at": resume.created_at
        }
