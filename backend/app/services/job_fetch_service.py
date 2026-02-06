"""
Job fetching service.
Handles fetching jobs from external APIs or using dummy data.
"""

import json
import random
from typing import Dict, List
from app.core.config import settings
from app.core.logger import logger

class JobFetchService:
    """
    Service for fetching job listings.
    """

    def __init__(self):
        # In production, this would use real APIs like Indeed, LinkedIn, etc.
        # For now, we'll use dummy data
        pass

    def search_jobs(self, query: str, location: str = None, limit: int = 20) -> List[Dict]:
        """
        Search for jobs based on query and location.

        Args:
            query: Job search query
            location: Job location (optional)
            limit: Maximum number of jobs to return

        Returns:
            List of job dictionaries
        """
        # Dummy job data for development
        dummy_jobs = [
            {
                "id": f"job_{i}",
                "title": f"Software Engineer {i}",
                "company": f"Tech Company {i}",
                "location": location or "San Francisco, CA",
                "description": f"We are looking for a skilled Software Engineer to join our team. Experience with {query} is preferred.",
                "requirements": f"3+ years experience, proficiency in {query}, Python, JavaScript",
                "salary_range": "$100,000 - $150,000",
                "job_type": "Full-time",
                "posted_date": "2024-01-01",
            }
            for i in range(1, limit + 1)
        ]

        # Filter by query (simple string matching)
        if query:
            filtered_jobs = [
                job for job in dummy_jobs
                if query.lower() in job["title"].lower() or query.lower() in job["description"].lower()
            ]
            return filtered_jobs[:limit]

        return dummy_jobs[:limit]

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific job.

        Args:
            job_id: External job ID

        Returns:
            Job details dictionary or None if not found
        """
        # In production, this would fetch from API
        # For now, return dummy data
        return {
            "id": job_id,
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "description": "Detailed job description...",
            "requirements": "Requirements...",
            "salary_range": "$100,000 - $150,000",
            "job_type": "Full-time",
            "posted_date": "2024-01-01",
        }
