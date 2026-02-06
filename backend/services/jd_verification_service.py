import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def verify_optimization(resume, optimization_result: dict, jd_text: str, intent: dict) -> dict:
    """
    Verifies the optimization and calculates a projected ATS score using LLM.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"ats_score": 0, "status": "Verification Skipped (No Key)"}

    try:
        client = OpenAI(api_key=api_key)
        
        new_summary = optimization_result.get("executive_summary", "")
        improvements = optimization_result.get("experience_improvements", [])
        improved_text = " ".join([i.get("improved", "") for i in improvements])
        
        prompt = f"""
        Act as an ATS (Applicant Tracking System).
        
        Job Description:
        {jd_text[:1000]}
        
        Optimized Resume Sections:
        Summary: {new_summary}
        Highlights: {improved_text}
        
        Evaluate the relevance of these optimized sections to the JD.
        Assign a projected ATS Match Score (0-100) and a Status (e.g., "Weak Match", "Good Match", "Strong Match").
        
        Return valid JSON:
        {{
            "ats_score": 85,
            "status": "Strong Match"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an ATS scoring algorithm. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "ats_score": 0,
            "status": f"Error: {str(e)}"
        }