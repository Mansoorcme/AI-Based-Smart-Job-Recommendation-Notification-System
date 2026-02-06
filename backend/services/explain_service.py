from openai import OpenAI
from models.resume import Resume
from models.job import Job
from models.match_result import MatchResult

def generate_explanation(resume: Resume, job: Job, match_result: MatchResult, api_key: str) -> str:
    if not api_key:
        return "LLM Explanation skipped (No API Key provided)."
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    Act as an expert ATS consultant. Analyze the match between the resume and the job description.
    
    Job Title: {job.title}
    Job Description: {job.description}
    Required Skills: {', '.join(job.required_skills)}
    
    Resume Skills: {', '.join(resume.skills)}
    Resume Experience: {resume.experience_years} years
    
    ATS Scores:
    - Overall: {match_result.final_score}%
    - Skills: {match_result.skill_match_score}%
    - Experience: {match_result.experience_match_score}%
    
    Provide a concise explanation (max 150 words):
    1. Why this is a good/bad match.
    2. What skills are missing.
    3. One specific improvement tip for the resume.
    """
    
    # Using standard chat completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()