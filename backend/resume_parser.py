"""
resume_parser.py — NLP + regex resume parser. Zero Gemini API calls.
"""

import re
from datetime import datetime
from io import BytesIO

import pdfplumber
import spacy

from config import (         # direct import
    SKILLS_DB, PHRASE_SKILLS, SINGLE_SKILLS,
    DOMAIN_MAP, SKILL_TO_ROLES, INDIA_LOCATIONS,
)

_nlp = spacy.load("en_core_web_sm")


def parse_pdf_bytes(file_bytes: bytes) -> str:
    """Extract plain text from a PDF given its raw bytes."""
    text = ""
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_work_section(text: str) -> str:
    """Isolate the Work Experience block, stopping at the next heading."""
    start_pat = re.compile(
        r"(?im)^[ \t]*(?:"
        r"work[\s\-]?experience|professional[\s\-]?experience|"
        r"employment(?:[\s\-]?history)?|career[\s\-]?history|work[\s\-]?history|"
        r"experience"
        r")[ \t]*:?\s*$"
    )
    end_pat = re.compile(
        r"(?im)^[ \t]*(?:"
        r"education|academic|qualification|projects?|skills?|"
        r"certifications?|achievements?|awards?|publications?|"
        r"languages?|interests?|summary|objective|about\s+me|"
        r"declaration|references?|hobbies|activities"
        r")[ \t]*:?\s*$"
    )
    m_start = start_pat.search(text)
    if not m_start:
        return ""
    after = text[m_start.end():]
    m_end = end_pat.search(after)
    return after[:m_end.start()] if m_end else after[:4000]


def calc_exp_from_ranges(work_text: str) -> float:
    """Sum months from all date ranges in the work section. Returns years as float."""
    MONTHS = {
        "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
        "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12,
    }
    pattern = re.compile(
        r"(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,\.\-]*)?"
        r"(\d{4})\s*[-–—to]+\s*"
        r"(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,\.\-]*)?"
        r"(\d{4}|present|current|till\s+date|till\s+now|ongoing|now)",
        work_text.lower(),
    )
    total_months = 0
    now = datetime.now()
    for m in pattern.finditer(work_text.lower()):
        try:
            s_mon_str, s_year_str = m.group(1), m.group(2)
            e_mon_str, e_raw      = m.group(3), m.group(4).strip()
            s_year = int(s_year_str)
            s_mon  = MONTHS.get((s_mon_str or "jan")[:3], 1)
            if re.match(r"(present|current|till|ongoing|now)", e_raw):
                e_year, e_mon = now.year, now.month
            else:
                e_year = int(e_raw)
                e_mon  = MONTHS.get((e_mon_str or "dec")[:3], 12)
            if s_year < 1995 or s_year > now.year or e_year < s_year:
                continue
            if e_year - s_year == 4 and e_mon <= 6:
                continue  # looks like a 4-year degree, skip
            total_months += max(0, (e_year - s_year) * 12 + (e_mon - s_mon))
        except Exception:
            pass
    return round(total_months / 12, 1)


def extract_resume_info(resume_text: str) -> dict:
    """
    Full NLP + regex resume parser.
    Returns dict: name, email, phone, location, skills, experience_years,
                  experience_level, experience_signals, domains, education, projects_count
    """
    text       = resume_text.strip()
    text_lower = text.lower()
    doc        = _nlp(text[:50000])

    # Email
    em    = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    email = em.group(0) if em else ""

    # Phone
    ph = re.search(r"(?:\+91[\s\-]?)?[6-9]\d{9}", text)
    if not ph:
        ph = re.search(r"(?:\+?\d[\s\-]?){10,13}", text)
    phone = ph.group(0).strip() if ph else ""

    # Name
    name = ""
    top_doc = _nlp("\n".join(text.split("\n")[:10]))
    for ent in top_doc.ents:
        if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
            name = ent.text.strip()
            break
    if not name:
        for line in text.split("\n")[:6]:
            ln = line.strip()
            if 2 <= len(ln.split()) <= 5 and ln.replace(" ","").isalpha() and ln[0].isupper():
                name = ln
                break

    # Location
    location = ""
    for ent in doc.ents:
        if ent.label_ in ("GPE","LOC") and ent.text.lower() in INDIA_LOCATIONS:
            location = ent.text.strip()
            break
    if not location:
        for city in INDIA_LOCATIONS:
            if re.search(rf"\b{city}\b", text_lower):
                location = city.title()
                break

    # Skills
    found = set()
    for phrase in PHRASE_SKILLS:
        if phrase in text_lower:
            found.add(phrase)
    for token in doc:
        tok = token.text.lower()
        if tok in SINGLE_SKILLS and len(tok) > 1:
            found.add(tok)
    toks = [t.text.lower() for t in doc]
    for i in range(len(toks) - 1):
        bg = toks[i] + " " + toks[i + 1]
        if bg in SKILLS_DB:
            found.add(bg)
    skills = sorted(found)

    # Domains
    domains = [d for d, ds in DOMAIN_MAP.items() if ds & found]

    # Experience
    work_section = extract_work_section(text)
    exp_years    = 0.0
    exp_signal   = "No work experience section found"

    if work_section:
        exp_years = calc_exp_from_ranges(work_section)
        explicit  = re.findall(
            r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s*(?:experience|exp)?",
            work_section.lower(),
        )
        if explicit:
            exp_years = max(exp_years, float(max(explicit, key=float)))
        exp_signal = f"{exp_years} year(s) from work date ranges"
    else:
        exp_signal = "Work Experience section not detected"

    intern_count   = len(re.findall(r"\b(?:intern(?:ship)?|trainee)\b", text_lower))
    fresher_signal = re.search(
        r"\b(?:fresher|b\.?tech|b\.?e\.?|bachelor|bsc|pursuing|final[\s\-]year|"
        r"recent[\s\-]graduate|passed[\s\-]out|class[\s\-]of[\s\-]20\d\d)\b",
        text_lower,
    )

    if exp_years == 0 and (not work_section or fresher_signal or intern_count > 0):
        exp_level  = "Fresher"
        exp_signal = f"No full-time work dates; {intern_count} internship(s) detected"
    elif exp_years <= 2:
        exp_level = "0-2 yrs"
    elif exp_years <= 4:
        exp_level = "2-4 yrs"
    else:
        exp_level = "5-10 yrs"

    # Education
    edu_m = re.search(
        r"(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|mba|bsc|msc|phd|bachelor|master|diploma)[^\n]{0,80}",
        text_lower,
    )
    education = edu_m.group(0).strip().title() if edu_m else ""

    # Projects count
    proj_verbs = len(re.findall(
        r"\b(?:built|developed|implemented|designed|created|deployed|architected)\b", text_lower,
    ))
    projects_count = max(proj_verbs // 2, 0)

    return {
        "name":               name,
        "email":              email,
        "phone":              phone,
        "location":           location,
        "skills":             skills,
        "experience_years":   round(exp_years, 1),
        "experience_level":   exp_level,
        "experience_signals": exp_signal,
        "domains":            domains,
        "education":          education,
        "projects_count":     projects_count,
    }
