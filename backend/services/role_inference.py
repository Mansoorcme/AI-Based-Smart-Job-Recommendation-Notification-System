import os
import google.genai as genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def infer_roles_and_ats(resume_text):
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
You are a technical recruiter.

From the resume below:
1. Suggest 3–5 realistic job roles for a fresher
2. For each role, provide:
   - Why it fits
   - Estimated ATS match percentage (strict)
   - Missing core skills

RESUME:
{resume_text}

Output in readable text (not JSON).
Be realistic and strict.
"""

    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
    return response.text
