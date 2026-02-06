"""
Career advisor agent.
Provides career guidance and recommendations.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.models.match_result import MatchResult
from app.services.llm_explain_service import LLMExplainService

class CareerAdvisorAgent:
    """
    Agent for providing career advice and recommendations.
    """

    def __init__(self):
        self.llm_service = LLMExplainService()

    def get_career_recommendations(
        self,
        user_id: int,
        db: Session,
        top_matches: int = 5
    ) -> Dict[str, any]:
        """
        Get personalized career recommendations based on match history.

        Args:
            user_id: User ID
            db: Database session
            top_matches: Number of top matches to analyze

        Returns:
            Career recommendations
        """
        try:
            # Get user's recent match results
            matches = (
                db.query(MatchResult)
                .filter(MatchResult.user_id == user_id)
                .order_by(MatchResult.ats_score.desc())
                .limit(top_matches)
                .all()
            )

            if not matches:
                return {
                    "recommendations": ["Upload your resume and try some job matches to get personalized recommendations."],
                    "insights": [],
                    "next_steps": ["Complete your profile", "Upload resume", "Search for jobs"]
                }

            # Analyze patterns
            high_matches = [m for m in matches if m.ats_score >= 70]
            medium_matches = [m for m in matches if 50 <= m.ats_score < 70]

            recommendations = []
            insights = []

            if high_matches:
                top_job = high_matches[0].job
                recommendations.append(f"Consider applying to {top_job.title} positions at {top_job.company}")
                insights.append(f"You have strong matches in {top_job.title} roles")

            if medium_matches:
                recommendations.append("Focus on gaining experience in high-demand skills from your medium matches")
                insights.append("Your profile shows potential in multiple areas with some skill gaps")

            # Generate LLM-powered advice
            advice = self._generate_career_advice(matches)

            return {
                "recommendations": recommendations,
                "insights": insights,
                "llm_advice": advice,
                "next_steps": [
                    "Apply to high-match positions",
                    "Address skill gaps identified in match results",
                    "Network with professionals in your target roles"
                ]
            }

        except Exception as e:
            logger.error(f"Error getting career recommendations for user {user_id}: {e}")
            return {
                "recommendations": ["Unable to generate recommendations at this time."],
                "insights": [],
                "next_steps": []
            }

    def _generate_career_advice(self, matches: List[MatchResult]) -> str:
        """
        Generate LLM-powered career advice.

        Args:
            matches: List of match results

        Returns:
            Career advice text
        """
        if not self.llm_service.client:
            return "Based on your matches, focus on roles where you score 70% or higher. Consider upskilling in areas where you have gaps."

        try:
            # Compile match data for LLM
            match_summary = "\n".join([
                f"- {match.job.title} at {match.job.company}: {match.ats_score:.1f}% match"
                for match in matches[:3]  # Top 3 matches
            ])

            prompt = f"""
            Based on these job match results, provide brief career advice (2-3 sentences):

            {match_summary}

            Focus on:
            1. Most promising career paths
            2. Key skills to develop
            3. Next steps for job search
            """

            response = self.llm_service.client.chat.completions.create(
                model=self.llm_service.client._model if hasattr(self.llm_service.client, '_model') else "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating career advice: {e}")
            return "Consider roles that align with your strongest matches and work on developing identified skill gaps."
