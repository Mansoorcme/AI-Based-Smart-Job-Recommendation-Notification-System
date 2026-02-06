"""
Validation utilities for API inputs.
"""

import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    """
    User creation schema.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserInDB(BaseModel):
    """
    User database schema.
    """
    id: int
    email: EmailStr
    full_name: str
    is_active: bool = True

    class Config:
        from_attributes = True

class JobSearch(BaseModel):
    """
    Job search parameters.
    """
    q: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    limit: int = Field(20, ge=1, le=100)

class ResumeUpload(BaseModel):
    """
    Resume upload schema.
    """
    filename: str

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        if not v:
            raise ValueError("Filename cannot be empty")

        # Check file extension
        allowed_extensions = {".pdf", ".doc", ".docx", ".txt"}
        file_ext = v.lower().rsplit(".", 1)[-1] if "." in v else ""

        if f".{file_ext}" not in allowed_extensions:
            raise ValueError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")

        return v

class MatchRequest(BaseModel):
    """
    ATS match request schema.
    """
    resume_id: int = Field(..., gt=0)
    job_id: int = Field(..., gt=0)

def validate_email(email: str) -> bool:
    """
    Validate email format.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> dict:
    """
    Check password strength and return requirements.
    """
    requirements = {
        "length": len(password) >= 8,
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "digit": bool(re.search(r"\d", password)),
        "special": bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    }

    requirements["strong"] = all(requirements.values())
    return requirements
