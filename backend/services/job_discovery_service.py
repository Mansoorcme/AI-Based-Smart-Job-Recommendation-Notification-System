import httpx
import asyncio
from typing import List, Dict, Any
from models.job import Job
from config import settings

class JobDiscoveryService:
    def __init__(self):
        self.client = None

    async def _get_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient()
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def discover_jobs(self, skills: List[str], max_results: int = 10) -> List[Job]:
        """
        Fetch jobs from Adzuna API based on provided skills.
        """
        app_id = settings.ADZUNA_APP_ID
        app_key = settings.ADZUNA_API_KEY

        if not app_id or not app_key:
            print("Adzuna credentials missing in settings.")
            return []

        # Construct search query from top skills
        what_query = " ".join(skills[:3]) if skills else "developer"
        
        # Adzuna API endpoint (using 'in' for India, change to 'us', 'gb' etc. as needed)
        country_code = "in"
        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
        
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": str(max_results),
            "what": what_query,
            "content-type": "application/json"
        }

        try:
            client = await self._get_client()
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return self._parse_adzuna_results(data.get('results', []))
            else:
                print(f"Adzuna API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error connecting to Adzuna: {e}")
            return []

    def _parse_adzuna_results(self, results: List[Dict[str, Any]]) -> List[Job]:
        jobs = []
        for item in results:
            # Adzuna doesn't always provide structured skills or min_experience, so we set defaults
            job = Job(
                id=str(item.get('id', '')),
                title=item.get('title', 'Unknown Role'),
                company=item.get('company', {}).get('display_name', 'Unknown Company'),
                description=item.get('description', 'No description provided.'),
                location=item.get('location', {}).get('display_name', ''),
                apply_link=item.get('redirect_url', ''),
                required_skills=[], 
                min_experience=0.0 
            )
            jobs.append(job)
        return jobs