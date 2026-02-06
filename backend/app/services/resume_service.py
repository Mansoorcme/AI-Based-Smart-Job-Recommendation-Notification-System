"""
Resume processing service.
Handles resume upload, text extraction, and parsing.
"""

import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional
import spacy
from app.core.config import settings
from app.core.logger import logger

class ResumeService:
    """
    Service for processing resumes.
    """

    def __init__(self):
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
        except OSError:
            logger.warning(f"spaCy model {settings.SPACY_MODEL} not found. Installing...")
            os.system(f"python -m spacy download {settings.SPACY_MODEL}")
            self.nlp = spacy.load(settings.SPACY_MODEL)

        # Create uploads directory if it doesn't exist
        self.upload_dir = Path("uploads/resumes")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_resume_file(self, file_content: bytes, filename: str, user_id: int) -> str:
        """
        Save uploaded resume file to disk.

        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User ID for organizing files

        Returns:
            File path where the file was saved
        """
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
        user_dir = self.upload_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)

        file_path = user_dir / unique_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"Saved resume file: {file_path}")
        return str(file_path)

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from resume file.

        Args:
            file_path: Path to the resume file

        Returns:
            Extracted text content
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        try:
            if path.suffix.lower() == ".pdf":
                return self._extract_from_pdf(file_path)
            elif path.suffix.lower() in [".doc", ".docx"]:
                return self._extract_from_docx(file_path)
            elif path.suffix.lower() == ".txt":
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {path.suffix}")

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise

    def parse_resume_content(self, text: str) -> Dict[str, any]:
        """
        Parse resume text to extract structured information.

        Args:
            text: Resume text content

        Returns:
            Dictionary with parsed information
        """
        doc = self.nlp(text.lower())

        # Extract skills (simple keyword-based approach)
        skills = self._extract_skills(doc)

        # Extract experience years (simple pattern matching)
        experience_years = self._extract_experience_years(text)

        # Extract education level
        education_level = self._extract_education_level(text)

        return {
            "skills": skills,
            "experience_years": experience_years,
            "education_level": education_level
        }

    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        """
        try:
            import PyPDF2
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.warning("PyPDF2 not installed, using fallback text extraction")
            return self._extract_from_txt(file_path)

    def _extract_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.
        """
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            logger.warning("python-docx not installed, using fallback text extraction")
            return self._extract_from_txt(file_path)

    def _extract_from_txt(self, file_path: str) -> str:
        """
        Extract text from TXT file.
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()

    def _extract_skills(self, doc) -> List[str]:
        """
        Extract skills from spaCy document.
        """
        # Common technical skills to look for
        common_skills = {
            "python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust",
            "react", "angular", "vue", "node.js", "django", "flask", "spring",
            "sql", "mysql", "postgresql", "mongodb", "redis",
            "aws", "azure", "gcp", "docker", "kubernetes", "git",
            "machine learning", "ai", "data science", "tensorflow", "pytorch",
            "agile", "scrum", "kanban", "devops", "ci/cd"
        }

        found_skills = []
        for token in doc:
            if token.text in common_skills:
                found_skills.append(token.text.title())

        return list(set(found_skills))  # Remove duplicates

    def _extract_experience_years(self, text: str) -> Optional[int]:
        """
        Extract years of experience from text.
        """
        import re

        # Look for patterns like "5 years", "3+ years", etc.
        patterns = [
            r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
            r"experience\s+(?:of\s+)?(\d+)\+?\s*years",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return max(int(match) for match in matches)

        return None

    def _extract_education_level(self, text: str) -> Optional[str]:
        """
        Extract education level from text.
        """
        education_keywords = {
            "phd": "PhD",
            "doctorate": "PhD",
            "masters": "Master's",
            "master's": "Master's",
            "bachelor": "Bachelor's",
            "bachelor's": "Bachelor's",
            "associate": "Associate",
            "high school": "High School"
        }

        text_lower = text.lower()
        for keyword, level in education_keywords.items():
            if keyword in text_lower:
                return level

        return None
