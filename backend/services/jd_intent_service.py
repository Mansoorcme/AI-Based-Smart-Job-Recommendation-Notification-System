import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def analyze_job_intent(jd_text: str) -> dict:
    """
    Analyzes the job description to determine the intent and role type using LLM.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Fallback if no API key
    if not api_key:
        jd_lower = jd_text.lower()
        role_type = "General"
        if "manager" in jd_lower or "lead" in jd_lower:
            role_type = "Management/Lead"
        elif "engineer" in jd_lower or "developer" in jd_lower:
            role_type = "Engineering"
        elif "analyst" in jd_lower:
            role_type = "Analyst"
        return {"role_type": role_type}

    try:
        import httpx
        # Create httpx client without proxies to avoid conflicts
        http_client = httpx.Client(proxies=None)
        client = OpenAI(api_key=api_key, http_client=http_client)
        
        prompt = f"""
        Analyze the following Job Description. Identify the Role Type (e.g., Engineering, Sales, Product), 
        Seniority Level, and Top 3 Key Technical Domains.
        
        Job Description:
        {jd_text[:1500]}
        
        Return a valid JSON object with keys: "role_type", "seniority", "domains".
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful job market analyst. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error in analyze_job_intent: {e}")
        return {"role_type": "General (Analysis Failed)"}