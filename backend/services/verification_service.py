"""
Verification Table Service.
Generates JD Requirement | Status | Evidence from Resume table.
"""

from typing import List, Dict, Any, Optional
from models.resume import Resume
from models.job import Job

class VerificationService:
    def generate_verification_table(
        self,
        resume: Resume,
        job: Job,
        jd_requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate verification table mapping JD requirements to resume evidence.

        Returns list of dicts with:
        - requirement: The JD requirement
        - status: matched/missing/partial
        - evidence: Text evidence from resume
        - confidence: 0-100 confidence score
        """
        verification_entries = []

        # 1. Degree requirements
        degree_entries = self._verify_degree_requirements(resume, job)
        verification_entries.extend(degree_entries)

        # 2. CGPA requirements
        cgpa_entries = self._verify_cgpa_requirements(resume, job)
        verification_entries.extend(cgpa_entries)

        # 3. Experience requirements
        exp_entries = self._verify_experience_requirements(resume, job)
        verification_entries.extend(exp_entries)

        # 4. Skill requirements
        skill_entries = self._verify_skill_requirements(resume, job)
        verification_entries.extend(skill_entries)

        # 5. Behavioral keywords
        behavioral_entries = self._verify_behavioral_keywords(resume, jd_requirements)
        verification_entries.extend(behavioral_entries)

        # 6. Tools and technologies
        tools_entries = self._verify_tools_technologies(resume, jd_requirements)
        verification_entries.extend(tools_entries)

        # 7. Compliance and SDLC terms
        compliance_entries = self._verify_compliance_sdlc(resume, jd_requirements)
        verification_entries.extend(compliance_entries)

        return verification_entries

    def _verify_degree_requirements(self, resume: Resume, job: Job) -> List[Dict[str, Any]]:
        """Verify degree requirements."""
        entries = []

        # Extract degree requirements from job description
        degree_reqs = self._extract_degree_requirements(job.description)

        for req in degree_reqs:
            evidence = self._find_degree_evidence(resume)
            status = self._determine_degree_status(req, evidence, resume.degree)
            confidence = self._calculate_degree_confidence(req, evidence, resume.degree)

            entries.append({
                "requirement": f"Degree: {req}",
                "status": status,
                "evidence": evidence or "No degree information found",
                "confidence": confidence,
                "category": "education"
            })

        return entries

    def _verify_cgpa_requirements(self, resume: Resume, job: Job) -> List[Dict[str, Any]]:
        """Verify CGPA requirements."""
        entries = []

        # Extract CGPA requirements from job description
        cgpa_reqs = self._extract_cgpa_requirements(job.description)

        for req in cgpa_reqs:
            evidence = self._find_cgpa_evidence(resume)
            status = self._determine_cgpa_status(req, evidence, resume.cgpa)
            confidence = self._calculate_cgpa_confidence(req, evidence, resume.cgpa)

            entries.append({
                "requirement": f"CGPA: {req}",
                "status": status,
                "evidence": evidence or "No CGPA information found",
                "confidence": confidence,
                "category": "education"
            })

        return entries

    def _verify_experience_requirements(self, resume: Resume, job: Job) -> List[Dict[str, Any]]:
        """Verify experience requirements."""
        entries = []

        exp_req = job.min_experience
        if exp_req > 0:
            evidence = f"{resume.experience_years} years of experience"
            status = "matched" if resume.experience_years >= exp_req else "missing"
            confidence = min(100, (resume.experience_years / exp_req) * 100) if exp_req > 0 else 100

            entries.append({
                "requirement": f"Experience: {exp_req}+ years",
                "status": status,
                "evidence": evidence,
                "confidence": round(confidence, 1),
                "category": "experience"
            })

        return entries

    def _verify_skill_requirements(self, resume: Resume, job: Job) -> List[Dict[str, Any]]:
        """Verify skill requirements."""
        entries = []

        for skill in job.required_skills:
            evidence = self._find_skill_evidence(resume, skill)
            status = "matched" if evidence else "missing"
            confidence = 90 if evidence else 0

            entries.append({
                "requirement": f"Skill: {skill}",
                "status": status,
                "evidence": evidence or f"No evidence of {skill} found",
                "confidence": confidence,
                "category": "technical"
            })

        return entries

    def _verify_behavioral_keywords(self, resume: Resume, jd_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify behavioral keywords."""
        entries = []

        for keyword in jd_requirements.get('behavioral_keywords', []):
            evidence = self._find_keyword_evidence(resume.text, keyword)
            status = "matched" if evidence else "missing"
            confidence = 85 if evidence else 0

            entries.append({
                "requirement": f"Behavioral: {keyword}",
                "status": status,
                "evidence": evidence or f"No evidence of {keyword} found",
                "confidence": confidence,
                "category": "behavioral"
            })

        return entries

    def _verify_tools_technologies(self, resume: Resume, jd_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify tools and technologies."""
        entries = []

        for tool in jd_requirements.get('tools_technologies', []):
            evidence = self._find_keyword_evidence(resume.text, tool)
            status = "matched" if evidence else "missing"
            confidence = 80 if evidence else 0

            entries.append({
                "requirement": f"Tool/Technology: {tool}",
                "status": status,
                "evidence": evidence or f"No evidence of {tool} found",
                "confidence": confidence,
                "category": "technical"
            })

        return entries

    def _verify_compliance_sdlc(self, resume: Resume, jd_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify compliance and SDLC terms."""
        entries = []

        for term in jd_requirements.get('compliance_sdlc', []):
            evidence = self._find_keyword_evidence(resume.text, term)
            status = "matched" if evidence else "missing"
            confidence = 75 if evidence else 0

            entries.append({
                "requirement": f"Compliance/SDLC: {term}",
                "status": status,
                "evidence": evidence or f"No evidence of {term} found",
                "confidence": confidence,
                "category": "compliance"
            })

        return entries

    def _extract_degree_requirements(self, job_description: str) -> List[str]:
        """Extract degree requirements from job description."""
        import re
        degrees = []

        # Common degree patterns
        patterns = [
            r'\b(Bachelor|Master|PhD|MBA|B\.Tech|M\.Tech|B\.E|M\.E|M\.S|B\.S)\b[^\w]*\b(of|in)\b[^\w]*\b([A-Za-z\s]+)\b',
            r'\b(Bachelor|Master|PhD|MBA|B\.Tech|M\.Tech|B\.E|M\.E|M\.S|B\.S)\b',
            r'\b(Engineering|Computer Science|IT|Business|Finance|Marketing)\b.*?\bdegree\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            degrees.extend([match[0] if isinstance(match, tuple) else match for match in matches])

        return list(set(degrees))  # Remove duplicates

    def _extract_cgpa_requirements(self, job_description: str) -> List[str]:
        """Extract CGPA requirements from job description."""
        import re
        cgpa_reqs = []

        # CGPA patterns
        patterns = [
            r'\b(CGPA|GPA)\b[^\w]*\b(\d+\.?\d*)\b',
            r'\b(\d+\.?\d*)\b[^\w]*\b(CGPA|GPA)\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    cgpa_reqs.append(f"{match[0]} {match[1]}")
                else:
                    cgpa_reqs.append(match)

        return cgpa_reqs

    def _find_degree_evidence(self, resume: Resume) -> Optional[str]:
        """Find degree evidence in resume."""
        if resume.degree:
            return f"Degree: {resume.degree}"
        return self._find_keyword_evidence(resume.text, r'\b(Bachelor|Master|PhD|MBA|B\.Tech|M\.Tech|B\.E|M\.E|M\.S|B\.S)\b')

    def _find_cgpa_evidence(self, resume: Resume) -> Optional[str]:
        """Find CGPA evidence in resume."""
        if resume.cgpa:
            return f"CGPA: {resume.cgpa}"
        return self._find_keyword_evidence(resume.text, r'\b(CGPA|GPA)\b[^\w]*\b(\d+\.?\d*)')

    def _find_skill_evidence(self, resume: Resume, skill: str) -> Optional[str]:
        """Find skill evidence in resume."""
        if skill.lower() in [s.lower() for s in resume.skills]:
            return f"Listed in skills section: {skill}"
        return self._find_keyword_evidence(resume.text, skill)

    def _find_keyword_evidence(self, text: str, keyword: str) -> Optional[str]:
        """Find keyword evidence in text."""
        import re
        pattern = re.compile(r'(.{0,50}' + re.escape(keyword) + r'.{0,50})', re.IGNORECASE)
        match = pattern.search(text)
        return match.group(0).strip() if match else None

    def _determine_degree_status(self, requirement: str, evidence: Optional[str], degree: Optional[str]) -> str:
        """Determine degree match status."""
        if not evidence and not degree:
            return "missing"
        if degree and requirement.lower() in degree.lower():
            return "matched"
        return "partial"

    def _determine_cgpa_status(self, requirement: str, evidence: Optional[str], cgpa: Optional[float]) -> str:
        """Determine CGPA match status."""
        if not evidence and cgpa is None:
            return "missing"
        # Extract CGPA value from requirement
        import re
        req_match = re.search(r'(\d+\.?\d*)', requirement)
        if req_match and cgpa:
            req_value = float(req_match.group(1))
            return "matched" if cgpa >= req_value else "missing"
        return "partial"

    def _calculate_degree_confidence(self, requirement: str, evidence: Optional[str], degree: Optional[str]) -> float:
        """Calculate confidence for degree match."""
        if degree and requirement.lower() in degree.lower():
            return 95.0
        if evidence:
            return 70.0
        return 0.0

    def _calculate_cgpa_confidence(self, requirement: str, evidence: Optional[str], cgpa: Optional[float]) -> float:
        """Calculate confidence for CGPA match."""
        if cgpa is not None:
            import re
            req_match = re.search(r'(\d+\.?\d*)', requirement)
            if req_match:
                req_value = float(req_match.group(1))
                if cgpa >= req_value:
                    return 90.0
        return 0.0
