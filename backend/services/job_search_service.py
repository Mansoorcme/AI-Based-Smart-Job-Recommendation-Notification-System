from typing import List
from models.job import Job

def search_jobs_from_career_pages(skills: List[str]) -> List[Job]:
    """
    Simulates fetching jobs from top 1000 career pages based on skills.
    In a production environment, this would connect to a job aggregator API 
    (like LinkedIn, Indeed, Google Jobs) or a custom scraper.
    """
    
    # Mock database of jobs from "Top Career Pages"
    # This represents the data gathered from external sources
    mock_jobs_db = [
        {
            "title": "Senior Software Engineer",
            "company": "Google",
            "description": "Build scalable systems. Experience with Python, Go, or Java required.",
            "skills": ["python", "java", "distributed systems", "cloud", "go"],
            "min_exp": 5.0,
            "link": "https://careers.google.com/jobs"
        },
        {
            "title": "Frontend Developer",
            "company": "Netflix",
            "description": "Create amazing user interfaces. React and TypeScript expert needed.",
            "skills": ["react", "typescript", "javascript", "css", "html"],
            "min_exp": 3.0,
            "link": "https://jobs.netflix.com/"
        },
        {
            "title": "Data Scientist",
            "company": "Amazon",
            "description": "Analyze large datasets to improve customer experience. Machine Learning and SQL proficiency required.",
            "skills": ["python", "machine learning", "sql", "aws", "pandas"],
            "min_exp": 2.0,
            "link": "https://www.amazon.jobs/"
        },
        {
            "title": "DevOps Engineer",
            "company": "Microsoft",
            "description": "Manage CI/CD pipelines and Azure infrastructure.",
            "skills": ["azure", "kubernetes", "docker", "ci/cd", "bash"],
            "min_exp": 4.0,
            "link": "https://careers.microsoft.com/"
        },
        {
            "title": "Backend Developer",
            "company": "Spotify",
            "description": "Backend development for streaming services. High performance API design.",
            "skills": ["python", "flask", "django", "api", "postgresql"],
            "min_exp": 3.0,
            "link": "https://www.lifeatspotify.com/"
        }
    ]
    
    found_jobs = []
    resume_skills_set = set(s.lower() for s in skills)
    
    for i, job_data in enumerate(mock_jobs_db):
        # Simple keyword matching to simulate search engine logic
        job_skills_set = set(s.lower() for s in job_data["skills"])
        
        # If there is an intersection of skills, we consider it a potential hit from the "web"
        if resume_skills_set.intersection(job_skills_set):
            found_jobs.append(Job(
                id=f"ext_{i}",
                title=job_data["title"],
                description=job_data["description"],
                required_skills=job_data["skills"],
                min_experience=job_data["min_exp"],
                company=job_data["company"],
                apply_link=job_data["link"]
            ))
            
    return found_jobs