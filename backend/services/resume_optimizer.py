from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def optimize_resume(resume_text, job_description):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
Act as a Big-4 resume consultant.

Resume:
{resume_text}

Job Description:
{job_description}

Provide:
- Persona shift
- Section-wise changes
- Skills reorganization
- Verification of eligibility

Human-readable output only.
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text
