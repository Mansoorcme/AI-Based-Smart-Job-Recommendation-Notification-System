"""
Configuration settings for the AI-Based Smart Job Recommendation & ATS Matching System.
Uses Pydantic for settings validation and environment variable loading.
"""

import secrets
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, ValidationInfo
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    """

    # Project settings
    PROJECT_NAME: str = "AI-Based Smart Job Recommendation & ATS Matching System"
    API_V1_STR: str = "/api/v1"

    # Server settings
    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    SERVER_PORT: int = 8000

    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Alternative port
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[str, List[str]]
    ) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database settings
    DATABASE_URL: str = "sqlite:///./app.db"  # Default to SQLite for dev

    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # ML/NLP settings
    SPACY_MODEL: str = "en_core_web_sm"

    # LLM settings (for explanations only)
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"

    # Gemini API settings (for role inference)
    GEMINI_API_KEY: Optional[str] = None

    # Job fetching settings
    JOBS_API_KEY: Optional[str] = None  # For real job APIs
    JOBS_PER_PAGE: int = 20

    # Adzuna API settings
    ADZUNA_APP_ID: Optional[str] = None
    ADZUNA_API_KEY: Optional[str] = None

    # Notification settings
    EMAIL_FROM: str = "noreply@jobmatch.com"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
