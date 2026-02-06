from models.resume import Resume
from models.job import Job
from models.match_result import MatchResult
import spacy
import warnings

# Load Spacy model safely
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # In a real app, you might trigger a download here or fail gracefully
    # For now, we assume the user has run: python -m spacy download en_core_web_sm
    print("Warning: Spacy model 'en_core_web_sm' not found. Similarity scores may be inaccurate.")
    nlp = spacy.blank("en")

def calculate_ats_score(resume: Resume, job: Job) -> MatchResult:
    # 1. Skill Match (40%)
    job_skills = set(job.required_skills)
    resume_skills = set(resume.skills)
    
    if not job_skills:
        skill_score = 100.0
    else:
        intersection = job_skills.intersection(resume_skills)
        skill_score = (len(intersection) / len(job_skills)) * 100

    # 2. Experience Match (15%)
    if job.min_experience <= 0:
        exp_score = 100.0
    else:
        # Cap at 100 if resume has more experience
        exp_score = min(resume.experience_years / job.min_experience, 1.0) * 100

    # 3. Role Similarity (25%) using Spacy vectors
    resume_doc = nlp(resume.text)
    job_doc = nlp(job.description)
    
    # Spacy similarity (0.0 to 1.0) -> convert to percentage
    # Note: en_core_web_sm doesn't have full vectors, so this is a heuristic approximation
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r"\[W007\]", category=UserWarning)
        role_similarity = resume_doc.similarity(job_doc) * 100
    role_similarity = max(role_similarity, 0.0)

    # 4. Keyword Match (20%)
    # Simple overlap of lemmatized nouns/verbs/adjectives
    resume_keywords = {token.lemma_.lower() for token in resume_doc if not token.is_stop and token.is_alpha}
    job_keywords = {token.lemma_.lower() for token in job_doc if not token.is_stop and token.is_alpha}
    
    if not job_keywords:
        keyword_score = 100.0
    else:
        keyword_overlap = resume_keywords.intersection(job_keywords)
        keyword_score = (len(keyword_overlap) / len(job_keywords)) * 100

    # Weighted Sum
    final_score = (
        (skill_score * 0.40) +
        (role_similarity * 0.25) +
        (keyword_score * 0.20) +
        (exp_score * 0.15)
    )

    return MatchResult(
        job_id=job.id,
        final_score=round(final_score, 2),
        skill_match_score=round(skill_score, 2),
        role_similarity_score=round(role_similarity, 2),
        keyword_match_score=round(keyword_score, 2),
        experience_match_score=round(exp_score, 2)
    )