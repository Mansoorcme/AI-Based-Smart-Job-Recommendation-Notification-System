"""
Role Inference Service.
Uses LLM to infer realistic job roles from resume content.
"""

import json
from typing import Dict, List, Optional
import google.genai as genai
from app.core.config import settings
from app.core.logger import logger

class RoleInferenceService:
    """
    Service for inferring job roles from resume content using LLM.
    """

    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            logger.warning("Gemini API key not configured. Role inference will be disabled.")

    def infer_roles(self, resume_text: str) -> Dict[str, any]:
        """
        Infer realistic job roles from resume content.

        Args:
            resume_text: Full resume text content

        Returns:
            Dictionary with role recommendations and explanations
        """
        if not self.client:
            return self._generate_fallback_roles()

        try:
            prompt = f"""
            ROLE:
            You are a senior technical recruiter and career advisor.

            SYSTEM CONTEXT:
            The resume has already been parsed and validated.
            Your task is to infer realistic job roles the candidate can apply for,
            based strictly on their skills, projects, and experience level.

            --------------------------------------------------
            INPUT
            --------------------------------------------------
            RESUME CONTENT:
            {resume_text}

            --------------------------------------------------
            OBJECTIVE
            --------------------------------------------------
            1) Identify the candidate's primary skill clusters
            2) Infer job roles that logically fit those skills
            3) Assume the candidate is a fresher or early-career professional
            4) Explain WHY each role is suitable

            Do NOT invent experience.
            Do NOT recommend senior roles.
            Be realistic and strict.

            --------------------------------------------------
            MANDATORY OUTPUT STRUCTURE
            --------------------------------------------------

            Start with a short diagnostic paragraph explaining
            how the skill combination positions the candidate in the job market.

            Then list roles using this EXACT structure:

            <Role Number>. <Job Role Name> (Junior / Associate)

            Explain:
            - Why this role fits the candidate
            - Which resume skills map directly to the role
            - What kind of work they would actually do

            Use this format for each role:

            Why you?
            <Explanation>

            Key Tasks:
            - <Task 1>
            - <Task 2>
            - <Task 3>

            --------------------------------------------------
            END WITH A DECISION GUIDE
            --------------------------------------------------
            Create a small comparison table:

            If you enjoy... | Target this role
            ----------------|------------------
            ...

            --------------------------------------------------
            STYLE RULES
            --------------------------------------------------
            - Human-readable
            - Professional but friendly
            - No ATS score
            - No job listings
            - No emojis
            - No generic advice

            Output as JSON with keys: "diagnostic", "roles" (list of role objects), "decision_guide"
            """

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Try to parse as JSON
            try:
                parsed = json.loads(result_text)
                return parsed
            except json.JSONDecodeError:
                # If not valid JSON, structure it manually
                return self._structure_response(result_text)

        except Exception as e:
            logger.error(f"Error inferring roles: {e}")
            return self._generate_fallback_roles()

    def _structure_response(self, response_text: str) -> Dict[str, any]:
        """
        Structure non-JSON response into expected format.
        """
        # Simple parsing - in production, use better parsing
        lines = response_text.split('\n')
        diagnostic = ""
        roles = []
        decision_guide = ""

        current_section = "diagnostic"
        current_role = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                if current_role:
                    roles.append(current_role)
                current_role = {"title": line, "explanation": "", "tasks": []}
                current_section = "role"
            elif current_section == "diagnostic" and not diagnostic:
                diagnostic = line
            elif current_role and "Why you?" in line:
                current_role["explanation"] = line.replace("Why you?", "").strip()
            elif current_role and "Key Tasks:" in line:
                current_section = "tasks"
            elif current_section == "tasks" and line.startswith("-"):
                current_role["tasks"].append(line[1:].strip())
            elif "If you enjoy" in line:
                current_section = "decision_guide"
                decision_guide += line + "\n"

        if current_role:
            roles.append(current_role)

        return {
            "diagnostic": diagnostic,
            "roles": roles,
            "decision_guide": decision_guide
        }

    def _generate_fallback_roles(self) -> Dict[str, any]:
        """
        Generate fallback role recommendations when LLM is not available.
        """
        return {
            "diagnostic": "Based on your resume, you have foundational technical skills suitable for entry-level positions in software development and data analysis.",
            "roles": [
                {
                    "title": "Junior Software Developer",
                    "explanation": "Your programming skills and project experience make you suitable for junior development roles.",
                    "tasks": [
                        "Write and maintain code for web applications",
                        "Debug and fix software issues",
                        "Collaborate with senior developers on projects"
                    ]
                },
                {
                    "title": "Data Analyst (Associate)",
                    "explanation": "Your analytical skills and data handling experience fit associate-level data roles.",
                    "tasks": [
                        "Analyze datasets to extract insights",
                        "Create reports and visualizations",
                        "Support data-driven decision making"
                    ]
                }
            ],
            "decision_guide": "If you enjoy coding and building applications | Target Junior Software Developer\nIf you prefer working with data and insights | Target Data Analyst (Associate)"
        }
