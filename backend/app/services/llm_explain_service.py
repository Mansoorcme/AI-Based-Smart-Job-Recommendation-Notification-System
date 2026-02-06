"""
LLM explanation service.
Uses LLM for generating explanations and resume improvement suggestions.
Note: LLM is ONLY used for explanations, not for scoring.
"""

import json
from typing import Dict, List, Optional
import openai
from app.core.config import settings
from app.core.logger import logger

class LLMExplainService:
    """
    Service for generating LLM-powered explanations and suggestions.
    """

    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai.OpenAI()
        else:
            logger.warning("OpenAI API key not configured. LLM explanations will be disabled.")

    def generate_match_explanation(
        self,
        resume_text: str,
        job_description: str,
        job_requirements: str,
        ats_score: float,
        component_scores: Dict[str, float]
    ) -> str:
        """
        Generate explanation for why the job matches the resume.

        Args:
            resume_text: Resume content
            job_description: Job description
            job_requirements: Job requirements
            ats_score: Overall ATS score
            component_scores: Individual component scores

        Returns:
            Explanation text
        """
        if not self.client:
            return self._generate_fallback_explanation(ats_score, component_scores)

        try:
            prompt = f"""
            Analyze this job match and explain why it fits the candidate's resume.

            Resume Content:
            {resume_text[:1000]}...  # Truncated for brevity

            Job Description:
            {job_description}

            Job Requirements:
            {job_requirements}

            ATS Match Score: {ats_score:.1f}%
            Component Scores:
            - Skill Match: {component_scores.get('skill_match_score', 0):.1f}%
            - Role Similarity: {component_scores.get('role_similarity_score', 0):.1f}%
            - Keyword Overlap: {component_scores.get('keyword_overlap_score', 0):.1f}%
            - Experience Match: {component_scores.get('experience_match_score', 0):.1f}%

            Provide a concise explanation (2-3 sentences) of why this job matches the resume,
            highlighting the strongest matching aspects.
            """

            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating LLM explanation: {e}")
            return self._generate_fallback_explanation(ats_score, component_scores)

    def generate_resume_improvements(
        self,
        resume_text: str,
        job_description: str,
        job_requirements: str,
        missing_skills: List[str]
    ) -> str:
        """
        Generate resume improvement suggestions.

        Args:
            resume_text: Resume content
            job_description: Job description
            job_requirements: Job requirements
            missing_skills: List of skills not found in resume

        Returns:
            Improvement suggestions text
        """
        if not self.client:
            return self._generate_fallback_improvements(missing_skills)

        try:
            prompt = f"""
            Suggest specific improvements to make this resume more ATS-friendly for the job.

            Resume Content:
            {resume_text[:1000]}...  # Truncated for brevity

            Job Description:
            {job_description}

            Job Requirements:
            {job_requirements}

            Missing Skills: {', '.join(missing_skills) if missing_skills else 'None identified'}

            Provide 3-5 specific, actionable suggestions to improve the resume's match for this job.
            Focus on keyword optimization, skill highlighting, and ATS best practices.
            """

            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating LLM improvements: {e}")
            return self._generate_fallback_improvements(missing_skills)

    def identify_missing_skills(
        self,
        resume_skills: List[str],
        job_description: str,
        job_requirements: str
    ) -> List[str]:
        """
        Identify skills mentioned in job but missing from resume.

        Args:
            resume_skills: Skills from resume
            job_description: Job description
            job_requirements: Job requirements

        Returns:
            List of missing skills
        """
        # Simple keyword-based approach (could be enhanced with LLM)
        job_text = f"{job_description} {job_requirements}".lower()
        resume_skills_lower = [skill.lower() for skill in resume_skills]

        # Common skills to check
        common_skills = [
            "python", "javascript", "java", "react", "node.js", "sql", "aws",
            "docker", "kubernetes", "git", "agile", "scrum", "machine learning"
        ]

        missing = []
        for skill in common_skills:
            if skill in job_text and skill not in resume_skills_lower:
                missing.append(skill.title())

        return missing

    def _generate_fallback_explanation(self, ats_score: float, component_scores: Dict[str, float]) -> str:
        """
        Generate fallback explanation when LLM is not available.
        """
        if ats_score >= 80:
            return "This job is an excellent match for your resume, with strong alignment across all criteria."
        elif ats_score >= 60:
            return "This job is a good match for your resume, with solid performance in key areas."
        elif ats_score >= 40:
            return "This job has moderate alignment with your resume. Consider highlighting relevant experience."
        else:
            return "This job has limited alignment with your resume. Significant improvements may be needed."

    def _generate_fallback_improvements(self, missing_skills: List[str]) -> str:
        """
        Generate fallback improvement suggestions when LLM is not available.
        """
        suggestions = [
            "Add relevant keywords from the job description to your resume.",
            "Quantify your achievements with specific metrics and results.",
            "Ensure your resume uses standard section headings (Experience, Education, Skills).",
            "Tailor your resume summary to highlight job-specific qualifications."
        ]

        if missing_skills:
            suggestions.insert(0, f"Consider adding these missing skills: {', '.join(missing_skills)}")

        return " • ".join(suggestions)
