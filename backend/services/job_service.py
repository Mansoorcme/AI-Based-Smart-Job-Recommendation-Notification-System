from typing import List, Optional
import asyncio
from models.job import Job
from services.job_discovery_service import JobDiscoveryService

def get_jobs(live: bool = False, skills: Optional[List[str]] = None) -> List[Job]:
    """
    Fetch jobs. If live=True and skills provided, attempts to fetch from external sources.
    Otherwise returns static mock data.
    """
    if live and skills:
        try:
            async def fetch_live():
                service = JobDiscoveryService()
                try:
                    return await service.discover_jobs(skills, max_results=10)
                finally:
                    await service.close()
            return asyncio.run(fetch_live())
        except Exception as e:
            print(f"Error fetching live jobs (falling back to static): {e}")

    # Mock data for the MVP
    return [
        Job(
            id="1",
            title="Senior Backend Engineer",
            description="We are looking for a Python expert with FastAPI and AWS experience to build scalable microservices.",
            required_skills=["python", "fastapi", "aws", "postgresql", "docker"],
            min_experience=5.0
        ),
        Job(
            id="2",
            title="Machine Learning Engineer",
            description="Build ML models using PyTorch and TensorFlow. NLP experience is a plus. Work on LLM integration.",
            required_skills=["python", "pytorch", "tensorflow", "machine learning", "nlp"],
            min_experience=3.0
        ),
        Job(
            id="3",
            title="Frontend Developer",
            description="Create responsive UI with React and TypeScript. Experience with Tailwind CSS is preferred.",
            required_skills=["javascript", "typescript", "react", "css", "html"],
            min_experience=2.0
        ),
        Job(
            id="4",
            title="Data Analyst",
            description="Analyze business data using SQL and Tableau. Python scripting for automation.",
            required_skills=["sql", "tableau", "python", "data analytics"],
            min_experience=1.0
        ),
        Job(
            id="5",
            title="Product Manager",
            description="Lead product development cycles. Agile and Scrum experience required.",
            required_skills=["product management", "agile", "scrum", "communication", "leadership"],
            min_experience=4.0
        )
    ]