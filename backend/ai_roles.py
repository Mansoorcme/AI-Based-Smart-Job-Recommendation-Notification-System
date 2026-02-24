"""
ai_roles.py — Role suggestions, keyword expansion, ATS scoring via Gemini.
"""

import re
import json

from config import SKILL_TO_ROLES, DOMAIN_MAP          # direct import
from gemini_client import gemini_generate               # direct import


def suggest_roles_from_skills(skills: list, domains: list) -> list:
    """Rule-based role suggestions — no API call."""
    domain_fallback = {
        "Machine Learning / AI": ["Machine Learning Engineer","AI Engineer"],
        "Data Science":          ["Data Scientist","Data Analyst"],
        "Backend":               ["Backend Developer","Software Engineer"],
        "Frontend":              ["Frontend Developer","UI Developer"],
        "Cloud / DevOps":        ["DevOps Engineer","Cloud Engineer"],
        "Data Engineering":      ["Data Engineer","Big Data Engineer"],
        "Cyber Security":        ["Security Engineer","Cyber Security Analyst"],
    }
    roles, seen = [], set()
    for skill in skills:
        for role in SKILL_TO_ROLES.get(skill, []):
            if role not in seen:
                seen.add(role); roles.append(role)
    for domain in domains:
        for role in domain_fallback.get(domain, []):
            if role not in seen:
                seen.add(role); roles.append(role)
    return roles[:8]


def expand_keywords_ai(user_query: str, skills: list) -> list:
    """Expand a keyword into 5-7 precise job title variants using Gemini."""
    prompt = f"""
You are a technical recruiter.
User typed: "{user_query}"
Candidate skills: {list(skills[:15])}
Expand into 5-7 precise job title search terms covering synonyms and related roles.
Respond ONLY as a JSON array of strings. No markdown, no explanation.
"""
    try:
        raw    = gemini_generate(prompt)
        result = json.loads(re.sub(r"```(?:json)?|```", "", raw).strip())
        return result if isinstance(result, list) else [user_query]
    except Exception:
        return [user_query]


def infer_roles_and_ats(skills: list) -> str:
    """Recommend roles + ATS scores using Gemini. Falls back to heuristics."""
    prompt = f"""
Act as an expert ATS system.
Candidate Skills: {', '.join(skills)}

Task:
1. Identify top 3-5 job roles suitable for this candidate.
2. For each role, calculate an estimated ATS Match Score (0-100%).
3. List matching skills and missing skills for each role.

Output Format (Markdown):
### 1. [Role Name] - [Score]% Match
- **Matching Skills:** ...
- **Missing Skills:** ...
- **Reasoning:** ...
"""
    try:
        return gemini_generate(prompt)
    except Exception as exc:
        return _heuristic_fallback(skills, exc)


def _heuristic_fallback(skills: list, error: Exception) -> str:
    norm = {s.strip().lower() for s in skills if s.strip()}
    pool = []
    for s in norm:
        pool.extend(SKILL_TO_ROLES.get(s, []))
    if not pool:
        pool = ["Software Engineer","Backend Developer","Data Analyst"]
    best = {}
    for role in pool:
        rk    = role.lower()
        score = min(95, max(45, 55 + sum(1 for s in norm if s in rk or rk in s) * 10))
        best[role] = max(score, best.get(role, 0))
    top = sorted(best.items(), key=lambda x: x[1], reverse=True)[:3]
    lines = [f"*Gemini unavailable — heuristic fallback. Reason: {error}*", ""]
    for i, (role, score) in enumerate(top, 1):
        lines += [
            f"### {i}. {role} - {score}% Match",
            f"- **Matching Skills:** {', '.join(sorted(norm)[:6]) or 'N/A'}",
            "- **Missing Skills:** Domain-specific tooling, measurable project impact",
            "- **Reasoning:** Estimated via skill/role-title overlap heuristic.", "",
        ]
    return "\n".join(lines).strip()


def parse_roles_output(roles_output: str) -> list:
    """Parse Markdown ATS output into list of row dicts."""
    def _field(text, field_name):
        pat = re.compile(
            rf"^(?:[-*]\s*)?(?:\d+[\).\s-]*)?(?:\*\*)?\s*{field_name}\s*(?:\*\*)?\s*[:\-]\s*(.+)$", re.I,
        )
        m = pat.match(text.strip())
        return m.group(1).strip() if m else None

    rows, current = [], None
    for raw in roles_output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("###"):
            if current:
                rows.append(current)
            m = re.match(r"^###\s*\d+\.?\s*(.+?)\s*-\s*(\d{1,3})%?\s*Match", line, re.I)
            if not m:
                m = re.match(r"^###\s*(?:\d+[\).\s-]*)?(.+?)\s*[\(\-]\s*(\d{1,3})%?\)?\s*$", line, re.I)
            current = ({"Role":m.group(1).strip(),"ATS Score":f"{m.group(2)}%",
                        "Matching Skills":"","Missing Skills":"","Reasoning":""} if m else None)
            continue
        if current:
            for field in ("matching skills","missing skills","reasoning"):
                v = _field(line, field)
                if v:
                    current[field.title()] = v
                    break
    if current:
        rows.append(current)
    for r in rows:
        r.setdefault("Matching Skills","N/A")
        r.setdefault("Missing Skills","N/A")
    return rows


def build_roles_markdown_table(rows: list) -> str:
    def _c(v): return (v or "").replace("|","/").replace("**","").strip()
    lines = ["| Role | ATS Score | Matching Skills | Missing Skills |","|----|---:|---|---|"]
    for r in rows:
        lines.append(f"| {_c(r.get('Role'))} | {_c(r.get('ATS Score'))} | {_c(r.get('Matching Skills'))} | {_c(r.get('Missing Skills'))} |")
    return "\n".join(lines)
