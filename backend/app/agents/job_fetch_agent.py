"""
Job fetch agent.
Coordinates job fetching and trust verification.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.services.job_fetch_service import JobFetchService
from app.services.trust_score_service import TrustScoreService

class JobFetchAgent:
    """
    Agent for handling job fetching operations.
    """

    def __init__(self):
        self.job_service = JobFetchService()
        self.trust_service = TrustScoreService()

    def search_and_verify_jobs(
        self,
        query: str,
        location: str = None,
        limit: int = 20
    ) -> List[Dict[str, any]]:
        """
        Search for jobs and verify their trustworthiness.

        Args:
            query: Job search query
            location: Job location
            limit: Maximum jobs to return

        Returns:
            List of verified job dictionaries
        """
        try:
            # Fetch jobs from service
            jobs = self.job_service.search_jobs(query, location, limit)

            # Verify each job
            verified_jobs = []
            for job in jobs:
                trust_score = self.trust_service.calculate_trust_score(job)

                # Only include jobs with acceptable trust scores
                if trust_score["trust_level"] != "low":
                    job["trust_score"] = trust_score
                    verified_jobs.append(job)

            logger.info(f"Found {len(verified_jobs)} verified jobs for query: {query}")
            return verified_jobs

        except Exception as e:
            logger.error(f"Error searching jobs for query {query}: {e}")
            return []

    def get_job_details_with_trust(
        self,
        job_id: str
    ) -> Optional[Dict[str, any]]:
        """
        Get job details with trust verification.

        Args:
            job_id: Job ID

        Returns:
            Job details with trust score
        """
        try:
            job = self.job_service.get_job_details(job_id)
            if not job:
                return None

            trust_score = self.trust_service.calculate_trust_score(job)
            job["trust_score"] = trust_score

            return job

        except Exception as e:
            logger.error(f"Error getting job details for {job_id}: {e}")
            return None

    def get_trust_statistics(self, jobs: List[Dict]) -> Dict[str, any]:
        """
        Calculate trust statistics for a list of jobs.

        Args:
            jobs: List of job dictionaries

        Returns:
            Trust statistics
        """
        if not jobs:
            return {"total_jobs": 0, "high_trust": 0, "medium_trust": 0, "low_trust": 0}

        trust_levels = [job.get("trust_score", {}).get("trust_level", "unknown") for job in jobs]

        return {
            "total_jobs": len(jobs),
            "high_trust": trust_levels.count("high"),
            "medium_trust": trust_levels.count("medium"),
            "low_trust": trust_levels.count("low"),
            "unknown_trust": trust_levels.count("unknown")
        }
