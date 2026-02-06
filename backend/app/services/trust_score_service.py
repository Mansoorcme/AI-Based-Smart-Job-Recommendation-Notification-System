"""
Trust score service for job verification.
Checks for fake or suspicious jobs.
"""

import re
from typing import Dict, Optional
from app.core.logger import logger

class TrustScoreService:
    """
    Service for calculating trust scores for jobs.
    """

    def __init__(self):
        # Trust indicators
        self.suspicious_domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "fakejob.com", "scamjob.com"  # Add known scam domains
        ]

        self.legitimate_domains = [
            "linkedin.com", "indeed.com", "monster.com", "glassdoor.com",
            "dice.com", "ziprecruiter.com"
        ]

    def calculate_trust_score(self, job_data: Dict) -> Dict[str, any]:
        """
        Calculate trust score for a job posting.

        Args:
            job_data: Job posting data

        Returns:
            Dictionary with trust score and reasons
        """
        score = 100  # Start with perfect score
        reasons = []

        # Check company email domain
        if "company_email" in job_data:
            domain = self._extract_domain(job_data["company_email"])
            if domain in self.suspicious_domains:
                score -= 30
                reasons.append("Suspicious email domain")
            elif domain in self.legitimate_domains:
                score += 10
                reasons.append("Legitimate job board domain")

        # Check for red flags in description
        description = job_data.get("description", "").lower()
        red_flags = [
            "work from home", "easy money", "guaranteed income",
            "no experience required", "immediate start", "urgent hiring"
        ]

        for flag in red_flags:
            if flag in description:
                score -= 10
                reasons.append(f"Contains '{flag}' - potential red flag")

        # Check salary range
        salary = job_data.get("salary_range", "")
        if "$" in salary:
            # Very high salaries might be suspicious
            if "500000" in salary.replace(",", "").replace("$", ""):
                score -= 20
                reasons.append("Unrealistically high salary")

        # Check posting date (very recent might be suspicious)
        # This would require date parsing in production

        # Ensure score doesn't go below 0
        score = max(0, score)

        trust_level = "high" if score >= 80 else "medium" if score >= 50 else "low"

        return {
            "trust_score": score,
            "trust_level": trust_level,
            "reasons": reasons,
            "is_suspicious": score < 50
        }

    def _extract_domain(self, email: str) -> Optional[str]:
        """
        Extract domain from email address.
        """
        match = re.search(r"@([\w.-]+)", email)
        return match.group(1) if match else None
