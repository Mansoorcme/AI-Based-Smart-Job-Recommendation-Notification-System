import re
from typing import List, Dict, Any

# A small sample DB of skills for MVP
SKILL_DB = {
    "python", "java", "c++", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "django", "flask", "fastapi", "sql", "postgresql", "mysql", "mongodb",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd", "machine learning",
    "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "communication", "leadership", "problem solving", "agile", "scrum", "html", "css",
    "rest api", "graphql", "linux", "bash"
}

# Job titles
TITLE_DB = {
    "software engineer", "senior software engineer", "junior software engineer",
    "data scientist", "machine learning engineer", "devops engineer", "backend developer",
    "frontend developer", "full stack developer", "product manager", "project manager",
    "qa engineer", "system administrator", "site reliability engineer", "sre"
}

# Certifications
CERT_DB = {
    "aws certified", "azure certified", "gcp certified", "csm", "cspo", "pmp",
    "cissp", "ceh", "comptia", "ccna", "ccnp", "kubernetes certified"
}

# Domain keywords
DOMAIN_DB = {
    "fraud detection", "natural language processing", "computer vision", "big data",
    "cloud computing", "microservices", "api development", "data analytics",
    "cybersecurity", "blockchain", "iot", "ai/ml", "distributed systems"
}

def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    found_skills = []
    for skill in SKILL_DB:
        # Simple regex to find whole words to avoid partial matches (e.g., "java" in "javascript")
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.append(skill)
    return found_skills

def extract_titles(text: str) -> List[str]:
    text_lower = text.lower()
    found_titles = []
    for title in TITLE_DB:
        if re.search(r'\b' + re.escape(title) + r'\b', text_lower):
            found_titles.append(title)
    return found_titles

def extract_certifications(text: str) -> List[str]:
    text_lower = text.lower()
    found_certs = []
    for cert in CERT_DB:
        if re.search(r'\b' + re.escape(cert) + r'\b', text_lower):
            found_certs.append(cert)
    return found_certs

def extract_domain_keywords(text: str) -> List[str]:
    text_lower = text.lower()
    found_domains = []
    for domain in DOMAIN_DB:
        if re.search(r'\b' + re.escape(domain.replace(' ', r'\s+')) + r'\b', text_lower):
            found_domains.append(domain)
    return found_domains

def extract_locations(text: str) -> List[str]:
    # Simple extraction of common locations
    locations = ["san francisco", "new york", "london", "berlin", "tokyo", "remote", "hybrid"]
    text_lower = text.lower()
    found_locations = []
    for loc in locations:
        if re.search(r'\b' + re.escape(loc) + r'\b', text_lower):
            found_locations.append(loc)
    return found_locations

def extract_experience(text: str) -> float:
    # Naive heuristic: look for "X years" or "X+ years"
    matches = re.findall(r'(\d+)\+?\s*years?', text.lower())
    if matches:
        try:
            return max(float(m) for m in matches)
        except ValueError:
            return 0.0
    return 0.0

def extract_resume_profile(text: str) -> Dict[str, Any]:
    """
    Extract normalized resume profile.
    """
    return {
        "skills": extract_skills(text),
        "job_titles": extract_titles(text),
        "certifications": extract_certifications(text),
        "domain_keywords": extract_domain_keywords(text),
        "location_preferences": extract_locations(text),
        "experience_years": extract_experience(text)
    }
