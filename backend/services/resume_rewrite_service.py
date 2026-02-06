import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def optimize_resume(resume, jd_text: str, intent: dict) -> dict:
    """
    Generates suggestions to optimize the resume based on the JD using Gemini LLM.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Google API Key is missing. Cannot perform optimization."}

    try:
        client = genai.Client(api_key=api_key)

        # Prepare context
        resume_excerpt = resume.text[:2000]
        role_focus = intent.get("role_type", "the target role")

        prompt = f"""
        You are an expert Resume Writer.
        Target Role: {role_focus}

        Job Description:
        {jd_text[:1000]}

        Candidate Resume Text (Excerpt):
        {resume_excerpt}

        Task:
        1. Rewrite the Executive Summary to specifically target this JD.
        2. Identify 2 weak or generic bullet points from the resume and rewrite them to be result-oriented (STAR method) matching JD keywords.

        Return a valid JSON object with this structure:
        {{
            "executive_summary": "New summary text...",
            "experience_improvements": [
                {{
                    "original": "Original bullet text...",
                    "improved": "Improved bullet text...",
                    "reason": "Why this is better..."
                }}
            ]
        }}
        """

        response = model.generate_content(prompt)
        # Gemini returns text, so we need to parse it as JSON
        result_text = response.text.strip()
        # Remove any markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()

        return json.loads(result_text)
    except Exception as e:
        return {"error": f"Optimization failed: {str(e)}"}
