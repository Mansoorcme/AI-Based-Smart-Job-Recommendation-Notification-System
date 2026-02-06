from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Job:
    id: str
    title: str
    description: str
    required_skills: List[str]
    min_experience: float
    company: str = "Unknown Company"
    apply_link: str = "#"
    posting_date: Optional[datetime] = None
    location: str = ""
    salary_range: Optional[str] = None
    job_type: str = "Full-time"
    source: str = ""
