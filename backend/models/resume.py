from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Resume:
    text: str
    skills: List[str] = field(default_factory=list)
    experience_years: float = 0.0
    file_name: str = ""
    degree: Optional[str] = None
    cgpa: Optional[float] = None
    roles: List[str] = field(default_factory=list)
