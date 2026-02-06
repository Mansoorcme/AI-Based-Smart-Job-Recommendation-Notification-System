from models.resume import Resume
from utils.resume_parser import parse_resume
from utils.skill_extractor import extract_skills, extract_experience
from utils.text_cleaner import clean_text

def process_resume(file_bytes: bytes, file_name: str) -> Resume:
    raw_text = parse_resume(file_bytes, file_name)
    cleaned = clean_text(raw_text)
    skills = extract_skills(cleaned)
    experience = extract_experience(raw_text) # Use raw text for regex context
    
    return Resume(
        text=raw_text,
        skills=skills,
        experience_years=experience,
        file_name=file_name
    )