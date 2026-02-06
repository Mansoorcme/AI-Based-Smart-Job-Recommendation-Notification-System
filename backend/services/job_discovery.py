import requests
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_jobs(role, location="india"):
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": os.getenv("ADZUNA_APP_ID"),
        "app_key": os.getenv("ADZUNA_API_KEY"),
        "what": role,
        "where": location,
        "results_per_page": 5,
        "sort_by": "date"
    }

    try:
        response = requests.get(url, params=params)
        return response.json().get("results", [])
    except Exception:
        return []