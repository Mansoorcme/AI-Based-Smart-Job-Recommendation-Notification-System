from dataclasses import dataclass
from typing import Optional

@dataclass
class MatchResult:
    job_id: str
    final_score: float
    skill_match_score: float
    role_similarity_score: float
    keyword_match_score: float
    experience_match_score: float
    explanation: Optional[str] = None