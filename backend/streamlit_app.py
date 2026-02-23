"""
AI Smart Job Alert System v5.0
P1 - Job Search: Adzuna API + portal.json career pages. Auto-suggest from skills if blank.
P2 - Company Portals tab removed; career pages embedded inside search results.
P3 - Email config removed from sidebar; collected inline inside Email Alerts tab.
P4 - Experience ONLY from Work Experience section date ranges. No education years bleed.
"""

import streamlit as st
import os, json, re, smtplib, threading, time, hashlib, ssl
from datetime import datetime, timedelta
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pdfplumber
import spacy
import requests
from bs4 import BeautifulSoup
import concurrent.futures
from google import genai
from dotenv import load_dotenv
from job_alerts import JobRadar
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER

# ─── CONFIG ───────────────────────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY", "").strip()
SMTP_SERVER    = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 587))
SMTP_USER_ENV  = os.getenv("SMTP_USER", "")
SMTP_PASS_ENV  = os.getenv("SMTP_PASS", "")

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

nlp    = spacy.load("en_core_web_sm")

GEMINI_MODELS = [
    os.getenv("GEMINI_MODEL", "").strip(),
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


def _get_candidate_gemini_models() -> list:
    if not gemini_client:
        return [m for m in GEMINI_MODELS if m]
    models = [m for m in GEMINI_MODELS if m]
    try:
        for m in gemini_client.models.list():
            name = getattr(m, "name", "") or ""
            if "gemini" not in name.lower():
                continue
            clean = name.split("/", 1)[1] if name.startswith("models/") else name
            if clean and clean not in models:
                models.append(clean)
    except Exception:
        pass
    return models

def gemini_generate(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing. Set it in backend/.env")
    if not gemini_client:
        raise RuntimeError("Gemini client not initialized.")
    last_err = None
    model_candidates = _get_candidate_gemini_models()
    if not model_candidates:
        raise RuntimeError("No Gemini models available.")
    for model_name in model_candidates:
        for attempt in range(3):
            try:
                r = gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return r.text
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    delay = 30 * (attempt + 1)
                    m = re.search(r"retryDelay.*?(\d+)s", err_str)
                    if m:
                        delay = int(m.group(1)) + 2
                    time.sleep(delay)
                    last_err = e
                else:
                    last_err = e
                    break
    raise RuntimeError(
        f"All Gemini models failed across {len(model_candidates)} model(s). Last: {last_err}"
    )

EXP_BUCKETS = {
    "Fresher" : ["intern", "trainee", "fresher", "entry level", "graduate", "junior"],
    "0-2 yrs" : ["junior", "associate", "entry level", "0-2 years"],
    "2-4 yrs" : ["mid-level", "2-4 years", "intermediate"],
    "5-10 yrs": ["senior", "lead", "principal", "5+ years"],
}

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Job Alert System", page_icon="🚀", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');
:root{--bg:#07070f;--card:#0f0f1a;--border:#22223a;--p:#7c6fff;--p2:#ff6b8a;--text:#e4e4f0;--muted:#7777a0;}
html,body,.stApp{background:var(--bg)!important;color:var(--text)!important;font-family:'DM Sans',sans-serif;}
h1,h2,h3,.mono{font-family:'Space Mono',monospace!important;}
.grad-text{background:linear-gradient(120deg,var(--p),var(--p2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.2rem 1.5rem;margin:.55rem 0;}
.card-l{border-left:3px solid var(--p);}
.card-p{border-left:3px solid var(--p2);}
.badge{display:inline-block;background:#1e1a40;border:1px solid #7c6fff44;color:#a8a4ff;
  padding:3px 11px;border-radius:20px;font-size:.78rem;margin:2px 3px;font-family:'Space Mono',monospace;}
.stButton>button{background:linear-gradient(135deg,var(--p),#9c6fff)!important;color:#fff!important;
  border:none!important;border-radius:8px!important;font-family:'Space Mono',monospace!important;
  font-size:.82rem!important;padding:.45rem 1.1rem!important;transition:.2s!important;}
.stButton>button:hover{opacity:.82!important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div>div{
  background:var(--card)!important;border:1px solid var(--border)!important;
  color:var(--text)!important;border-radius:8px!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--card)!important;border-radius:10px!important;padding:4px!important;}
.stTabs [data-baseweb="tab"]{color:var(--muted)!important;font-family:'Space Mono',monospace!important;font-size:.78rem!important;}
.stTabs [aria-selected="true"]{background:var(--p)!important;color:#fff!important;border-radius:8px!important;}
div[data-testid="stSidebar"]{background:var(--card)!important;border-right:1px solid var(--border)!important;}
.metric-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:.9rem;text-align:center;}
.metric-num{font-family:'Space Mono',monospace;font-size:1.8rem;
  background:linear-gradient(120deg,var(--p),var(--p2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.metric-lbl{font-size:.75rem;color:var(--muted);margin-top:3px;}
.info-box{background:#0d1a3a;border:1px solid #2d4f9a55;border-radius:8px;padding:.7rem 1rem;color:#7aaaff;font-size:.85rem;margin:.4rem 0;}
.success-box{background:#0d2e1a;border:1px solid #2d7a4f55;border-radius:8px;padding:.7rem 1rem;color:#5dba85;font-size:.85rem;margin:.4rem 0;}
.warn-box{background:#2e1f0d;border:1px solid #9a7a2d55;border-radius:8px;padding:.7rem 1rem;color:#d4aa50;font-size:.85rem;margin:.4rem 0;}
a.apply-btn{display:inline-block;background:linear-gradient(135deg,var(--p),#9c6fff);
  color:#fff!important;padding:6px 16px;border-radius:7px;font-size:.8rem;
  text-decoration:none;font-family:'Space Mono',monospace;margin-top:6px;}
a.apply-btn:hover{opacity:.82;}
a.portal-btn{display:inline-block;background:linear-gradient(135deg,var(--p2),#ff4f7b);
  color:#fff!important;padding:6px 16px;border-radius:7px;font-size:.8rem;
  text-decoration:none;font-family:'Space Mono',monospace;margin-top:6px;}
a.portal-btn:hover{opacity:.82;}
.tag{display:inline-block;font-size:.7rem;padding:2px 9px;border-radius:10px;margin-bottom:6px;}
.tag-live{background:#7c6fff;color:white;}
.tag-portal{background:#ff6b8a;color:white;}
hr.thin{border:none;border-top:1px solid var(--border);margin:.8rem 0;}
</style>
""", unsafe_allow_html=True)

# ─── LOAD PORTALS ─────────────────────────────────────────────────────────────
@st.cache_data
def load_portals():
    candidates = [
        os.path.join(os.path.dirname(__file__), "Portal__1_.json"),
        "/mnt/user-data/uploads/Portal__1_.json",
        "Portal__1_.json",
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as f:
                raw = json.load(f)
            out = []
            for item in raw:
                link = item["Link"].strip()
                if not link.startswith("http"):
                    link = "https://" + link
                out.append({"title": item["Title"].strip(), "link": link})
            return out
    return []

PORTALS = load_portals()
# Quick lookup: lowercase title → portal dict
PORTAL_MAP = {p["title"].lower(): p for p in PORTALS}

# ─── SKILLS DATABASE ──────────────────────────────────────────────────────────
SKILLS_DB = {
    "python","java","javascript","typescript","c++","c#","c","go","golang","rust",
    "kotlin","swift","scala","r","matlab","perl","php","ruby","dart","julia",
    "html","css","react","reactjs","angular","vue","vuejs","nextjs","nodejs",
    "express","django","flask","fastapi","spring","springboot","asp.net",
    "tailwind","bootstrap","sass","graphql","rest","restful api","websocket",
    "machine learning","deep learning","nlp","natural language processing",
    "computer vision","data science","data analysis","data engineering",
    "tensorflow","pytorch","keras","scikit-learn","sklearn","xgboost","lightgbm",
    "pandas","numpy","matplotlib","seaborn","plotly","opencv","huggingface",
    "transformers","bert","gpt","llm","generative ai","reinforcement learning",
    "sql","mysql","postgresql","mongodb","redis","elasticsearch","cassandra",
    "sqlite","oracle","dynamodb","firebase","supabase","neo4j","bigquery",
    "aws","azure","gcp","google cloud","docker","kubernetes","terraform",
    "jenkins","ci/cd","github actions","ansible","linux","bash","shell",
    "nginx","apache","microservices","serverless","lambda",
    "hadoop","spark","kafka","airflow","dbt","tableau","power bi","looker",
    "excel","snowflake","databricks","hive","flink","redshift",
    "git","github","gitlab","jira","agile","scrum","devops","mlops","api",
    "postman","swagger","figma","selenium","pytest","junit",
    "cybersecurity","cyber security","penetration testing","ethical hacking",
    "network security","siem","soc","vulnerability assessment","owasp",
    "blockchain","web3","solidity","iot","embedded systems","robotics",
    "image processing","signal processing","optimization","statistics",
}
PHRASE_SKILLS = sorted([s for s in SKILLS_DB if " " in s], key=len, reverse=True)
SINGLE_SKILLS = {s for s in SKILLS_DB if " " not in s}

DOMAIN_MAP = {
    "Machine Learning / AI": {"machine learning","deep learning","nlp","computer vision",
        "tensorflow","pytorch","keras","scikit-learn","xgboost","huggingface",
        "transformers","bert","gpt","llm","generative ai","reinforcement learning"},
    "Data Science":    {"data science","data analysis","pandas","numpy","matplotlib",
        "seaborn","tableau","power bi","statistics","bigquery","spark","hadoop"},
    "Backend":         {"python","java","nodejs","django","flask","fastapi","spring",
        "microservices","rest","restful api","sql","postgresql","redis","docker"},
    "Frontend":        {"react","reactjs","angular","vue","vuejs","nextjs","html","css",
        "javascript","typescript","tailwind","bootstrap","figma"},
    "Cloud / DevOps":  {"aws","azure","gcp","docker","kubernetes","terraform","jenkins",
        "ci/cd","ansible","serverless","linux"},
    "Data Engineering":{"spark","kafka","airflow","dbt","hadoop","snowflake",
        "databricks","hive","flink","redshift","data engineering"},
    "Cyber Security":  {"cybersecurity","cyber security","penetration testing",
        "ethical hacking","network security","siem","soc","owasp"},
}

# Skill → suggested job roles (used when user leaves query blank)
SKILL_TO_ROLES = {
    "python":           ["Python Developer","Backend Engineer"],
    "machine learning": ["Machine Learning Engineer","ML Engineer","AI Engineer"],
    "deep learning":    ["Deep Learning Engineer","AI Researcher"],
    "nlp":              ["NLP Engineer","Computational Linguist"],
    "data science":     ["Data Scientist","Data Analyst"],
    "data analysis":    ["Data Analyst","Business Analyst"],
    "data engineering": ["Data Engineer","ETL Developer"],
    "tensorflow":       ["ML Engineer","AI Engineer"],
    "pytorch":          ["Deep Learning Engineer","ML Researcher"],
    "react":            ["Frontend Developer","React Developer"],
    "nodejs":           ["Backend Developer","Node.js Developer"],
    "django":           ["Django Developer","Python Backend Developer"],
    "sql":              ["Database Administrator","Data Analyst"],
    "aws":              ["Cloud Engineer","AWS Solutions Architect"],
    "docker":           ["DevOps Engineer","Cloud Engineer"],
    "kubernetes":       ["DevOps Engineer","Platform Engineer"],
    "java":             ["Java Developer","Backend Engineer"],
    "cybersecurity":    ["Security Engineer","Penetration Tester"],
    "spark":            ["Data Engineer","Big Data Engineer"],
    "kafka":            ["Data Engineer","Platform Engineer"],
    "llm":              ["AI Engineer","LLM Engineer","GenAI Developer"],
    "generative ai":    ["GenAI Developer","AI Engineer"],
    "blockchain":       ["Blockchain Developer","Web3 Developer"],
    "javascript":       ["Frontend Developer","Full Stack Developer"],
    "typescript":       ["Frontend Developer","Full Stack Developer"],
    "angular":          ["Frontend Developer","Angular Developer"],
    "vue":              ["Frontend Developer","Vue Developer"],
    "go":               ["Backend Engineer","Go Developer"],
    "rust":             ["Systems Engineer","Rust Developer"],
    "scala":            ["Data Engineer","Scala Developer"],
    "c++":              ["Systems Engineer","Embedded Developer"],
    "devops":           ["DevOps Engineer","Platform Engineer"],
    "mlops":            ["MLOps Engineer","ML Platform Engineer"],
}

# Domain → good companies from portal list to highlight
DOMAIN_TO_COMPANIES = {
    "Machine Learning / AI": ["Google","Amazon","Microsoft","Meta","Adobe","Zoho","Freshworks",
                               "Flipkart","Samsung","Qualcomm"],
    "Data Science":          ["TCS","Infosys","Wipro","Accenture","Capgemini","IBM",
                               "Mu Sigma","Latentview Analytics"],
    "Backend":               ["Amazon","Flipkart","Zomato","Swiggy","Paytm","Ola",
                               "BrowserStack","Atlassian","Freshworks"],
    "Frontend":              ["Accenture","Capgemini","Wipro","Zoho","BrowserStack","Atlassian"],
    "Cloud / DevOps":        ["Amazon","Microsoft","Google","IBM","Oracle","Bosch"],
    "Data Engineering":      ["Amazon","Microsoft","Google","Databricks","TCS","Infosys"],
    "Cyber Security":        ["Wipro","TCS","IBM","Palo Alto Networks","Aujas"],
}

INDIA_LOCATIONS = {
    "hyderabad","bangalore","bengaluru","chennai","mumbai","pune","delhi","noida",
    "gurugram","gurgaon","kolkata","ahmedabad","jaipur","kochi","coimbatore",
    "indore","bhopal","lucknow","chandigarh","vizag","visakhapatnam","remote","india",
}

# ─── EXPERIENCE SECTION EXTRACTOR ─────────────────────────────────────────────
def _extract_work_section(text: str) -> str:
    """
    Isolate the Work Experience block only.
    Stops at the next major heading so education year ranges don't bleed in.
    """
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


def _calc_exp_from_ranges(work_text: str) -> float:
    """
    Parse all date ranges in the work section and sum total months.
    Handles:
      - Jan 2021 – Dec 2023
      - 2020 – Present / Current / Till Date / Ongoing
      - March 2019 to June 2021
    Returns total years as float.
    """
    MONTHS = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
              "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}

    pattern = re.compile(
        r"(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,\.\-]*)?(\d{4})"
        r"\s*[-–—to]+\s*"
        r"(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,\.\-]*)?(\d{4}|present|current|till\s+date|till\s+now|ongoing|now)",
        work_text.lower()
    )

    total_months = 0
    now = datetime.now()

    for m in pattern.finditer(work_text.lower()):
        try:
            s_mon_str, s_year_str, e_mon_str, e_raw = m.group(1), m.group(2), m.group(3), m.group(4)

            s_year = int(s_year_str)
            s_mon  = MONTHS.get((s_mon_str or "jan")[:3], 1)

            e_raw = e_raw.strip()
            if re.match(r"(present|current|till|ongoing|now)", e_raw):
                e_year = now.year
                e_mon  = now.month
            else:
                e_year = int(e_raw)
                e_mon  = MONTHS.get((e_mon_str or "dec")[:3], 12)

            # Skip impossible/education year ranges
            if s_year < 1995 or s_year > now.year or e_year < s_year:
                continue
            # Skip ranges that look like graduation (s_year == e_year and short)
            if e_year - s_year == 4 and e_mon <= 6:
                # Likely 4-year degree — skip
                continue

            months = max(0, (e_year - s_year) * 12 + (e_mon - s_mon))
            total_months += months
        except Exception:
            pass

    return round(total_months / 12, 1)


# ─── NLP RESUME PARSER ────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def parse_resume_bytes(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


@st.cache_data(show_spinner=False)
def extract_info_from_resume(resume_text: str) -> dict:
    """Pure NLP + regex resume parser — zero Gemini API calls."""
    text       = resume_text.strip()
    text_lower = text.lower()
    doc        = nlp(text[:50000])

    # ── EMAIL ─────────────────────────────────────────────────────────────────
    em    = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    email = em.group(0) if em else ""

    # ── PHONE ─────────────────────────────────────────────────────────────────
    ph    = re.search(r"(?:\+91[\s\-]?)?[6-9]\d{9}", text)
    if not ph:
        ph = re.search(r"(?:\+?\d[\s\-]?){10,13}", text)
    phone = ph.group(0).strip() if ph else ""

    # ── NAME ──────────────────────────────────────────────────────────────────
    name = ""
    top_doc = nlp("\n".join(text.split("\n")[:10]))
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

    # ── LOCATION ──────────────────────────────────────────────────────────────
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

    # ── SKILLS ────────────────────────────────────────────────────────────────
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

    # ── DOMAINS ───────────────────────────────────────────────────────────────
    domains = [d for d, ds in DOMAIN_MAP.items() if ds & found]

    # ── EXPERIENCE — P4 FIX: only from Work Experience section ───────────────
    work_section = _extract_work_section(text)

    exp_years = 0.0
    exp_signal = "No work experience section found"

    if work_section:
        exp_years = _calc_exp_from_ranges(work_section)

        # Also honour explicit "X years of experience" mentions inside work section
        explicit = re.findall(
            r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s*(?:experience|exp)?",
            work_section.lower()
        )
        if explicit:
            explicit_max = float(max(explicit, key=float))
            exp_years = max(exp_years, explicit_max)

        exp_signal = f"{exp_years} year(s) from work date ranges"
    else:
        # No explicit work section found — check for internships / fresher signals
        exp_signal = "Work Experience section not detected; using fresher signals"

    # Internship / fresher signals from full text
    intern_count   = len(re.findall(r"\b(?:intern(?:ship)?|trainee)\b", text_lower))
    fresher_signal = re.search(
        r"\b(?:fresher|b\.?tech|b\.?e\.?|bachelor|bsc|pursuing|final[\s\-]year|"
        r"recent[\s\-]graduate|passed[\s\-]out|class[\s\-]of[\s\-]20\d\d)\b",
        text_lower
    )

    # Classify
    if exp_years == 0 and (not work_section or fresher_signal or intern_count > 0):
        exp_level  = "Fresher"
        exp_signal = f"No full-time work dates; {intern_count} internship(s) detected"
    elif exp_years <= 2:
        exp_level  = "0-2 yrs"
    elif exp_years <= 4:
        exp_level  = "2-4 yrs"
    else:
        exp_level  = "5-10 yrs"

    # ── EDUCATION ─────────────────────────────────────────────────────────────
    edu_m = re.search(
        r"(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|mba|bsc|msc|phd|bachelor|master|diploma)[^\n]{0,80}",
        text_lower
    )
    education = edu_m.group(0).strip().title() if edu_m else ""

    # ── PROJECTS COUNT ────────────────────────────────────────────────────────
    proj_verbs = len(re.findall(
        r"\b(?:built|developed|implemented|designed|created|deployed|architected)\b",
        text_lower
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


# ─── JOB SEARCH HELPERS ───────────────────────────────────────────────────────
def suggest_roles_from_skills(skills: list, domains: list) -> list:
    """Build role list from resume skills — no API call needed."""
    roles, seen = [], set()
    for skill in skills:
        for role in SKILL_TO_ROLES.get(skill, []):
            if role not in seen:
                seen.add(role); roles.append(role)
    domain_fallback = {
        "Machine Learning / AI": ["Machine Learning Engineer","AI Engineer"],
        "Data Science":          ["Data Scientist","Data Analyst"],
        "Backend":               ["Backend Developer","Software Engineer"],
        "Frontend":              ["Frontend Developer","UI Developer"],
        "Cloud / DevOps":        ["DevOps Engineer","Cloud Engineer"],
        "Data Engineering":      ["Data Engineer","Big Data Engineer"],
        "Cyber Security":        ["Security Engineer","Cyber Security Analyst"],
    }
    for d in domains:
        for role in domain_fallback.get(d, []):
            if role not in seen:
                seen.add(role); roles.append(role)
    return roles[:8]


@st.cache_data(show_spinner=False)
def expand_keywords_ai(user_query: str, skills: tuple) -> list:
    """Use Gemini to expand a short keyword into precise job titles."""
    prompt = f"""
You are a technical recruiter.
User typed: "{user_query}"
Candidate skills: {list(skills[:15])}

Expand into 5-7 precise job title search terms covering synonyms and related roles.
Respond ONLY as a JSON array of strings. No markdown, no explanation.
"""
    try:
        text   = gemini_generate(prompt)
        result = json.loads(re.sub(r"```(?:json)?|```", "", text).strip())
        return result if isinstance(result, list) else [user_query]
    except Exception:
        return [user_query]


@st.cache_data(show_spinner=False)
def infer_roles_and_ats(skills: list) -> str:
    """Infer suitable roles and calculate ATS score based on skills."""
    prompt = f"""
    Act as an expert ATS system.
    Candidate Skills: {', '.join(skills)}
    
    Task:
    1. Identify top 3-5 job roles suitable for this candidate.
    2. For each role, calculate an estimated ATS Match Score (0-100%) based on the skills.
    3. List key matching skills and missing skills for each role.
    
    Output Format (Markdown):
    ### 1. [Role Name] - [Score]% Match
    - **Matching Skills:** ...
    - **Missing Skills:** ...
    - **Reasoning:** ...
    
    Keep it concise and professional.
    """
    try:
        return gemini_generate(prompt)
    except Exception as e:
        # Fallback path so the UI still works even if Gemini models are unavailable.
        norm_skills = {s.strip().lower() for s in skills if s and s.strip()}
        role_pool = []
        for s in norm_skills:
            role_pool.extend(SKILL_TO_ROLES.get(s, []))
        if not role_pool:
            role_pool = ["Software Engineer", "Backend Developer", "Data Analyst"]

        ranked_roles = []
        for role in role_pool:
            role_key = role.lower()
            overlap = sum(
                1 for s in norm_skills if s in role_key or role_key in s
            )
            score = min(95, max(45, 55 + overlap * 10))
            ranked_roles.append((role, score))

        # Deduplicate while preserving highest score per role.
        best = {}
        for role, score in ranked_roles:
            best[role] = max(score, best.get(role, 0))
        top_roles = sorted(best.items(), key=lambda x: x[1], reverse=True)[:3]

        lines = [
            "Gemini unavailable, showing heuristic fallback recommendations.",
            f"Reason: {e}",
            "",
        ]
        for idx, (role, score) in enumerate(top_roles, start=1):
            lines.append(f"### {idx}. {role} - {score}% Match")
            lines.append(
                f"- **Matching Skills:** {', '.join(sorted(norm_skills)[:6]) or 'N/A'}"
            )
            lines.append("- **Missing Skills:** Domain-specific tooling, measurable project impact")
            lines.append("- **Reasoning:** Estimated using role-title/skill overlap heuristic.")
            lines.append("")
        return "\n".join(lines).strip()


def roles_output_to_rows(roles_output: str) -> list:
    def _extract_field(text: str, field_name: str):
        # Supports variants like:
        # - **Matching Skills:** ...
        # Matching Skills: ...
        # 1) Matching skills - ...
        pat = re.compile(
            rf"^(?:[-*]\s*)?(?:\d+[\).\s-]*)?(?:\*\*)?\s*{field_name}\s*(?:\*\*)?\s*[:\-]\s*(.+)$",
            re.I,
        )
        m = pat.match(text.strip())
        return m.group(1).strip() if m else None

    rows = []
    current = None
    for raw in roles_output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("###"):
            if current:
                rows.append(current)
            m = re.match(r"^###\s*\d+\.?\s*(.+?)\s*-\s*(\d{1,3})%?\s*Match", line, re.I)
            if not m:
                # Alternate header formats:
                # ### Data Scientist (82%)
                # ### 1) Data Scientist - 82%
                m = re.match(r"^###\s*(?:\d+[\).\s-]*)?(.+?)\s*[\(\-]\s*(\d{1,3})%?\)?\s*$", line, re.I)
            if m:
                current = {
                    "Role": m.group(1).strip(),
                    "ATS Score": f"{m.group(2)}%",
                    "Matching Skills": "",
                    "Missing Skills": "",
                    "Reasoning": "",
                }
            else:
                current = None
            continue

        if current:
            v = _extract_field(line, "matching skills")
            if v:
                current["Matching Skills"] = v
                continue
            v = _extract_field(line, "missing skills")
            if v:
                current["Missing Skills"] = v
                continue
            v = _extract_field(line, "reasoning")
            if v:
                current["Reasoning"] = v
                continue

    if current:
        rows.append(current)

    # Keep table populated even when model omits some sections.
    for r in rows:
        if not r.get("Matching Skills"):
            r["Matching Skills"] = "N/A"
        if not r.get("Missing Skills"):
            r["Missing Skills"] = "N/A"

    return rows


def build_roles_markdown_table(rows: list) -> str:
    def _clean(v: str) -> str:
        text = (v or "").replace("|", "/")
        text = text.replace("**", "").replace("__", "")
        return text.strip()
    table = [
        "| Role | ATS Score | Matching Skills | Missing Skills |",
        "|---|---:|---|---|",
    ]
    for r in rows:
        table.append(
            f"| {_clean(r.get('Role',''))} | {_clean(r.get('ATS Score',''))} | "
            f"{_clean(r.get('Matching Skills',''))} | {_clean(r.get('Missing Skills',''))} |"
        )
    return "\n".join(table)


def fetch_adzuna_jobs(role: str, country: str, exp_level: str, location: str, n: int = 6) -> tuple:
    """
    Returns (results: list, error: str|None).
    Builds a smart query: role + experience modifier appended directly to `what`.
    """
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return [], "Missing ADZUNA_APP_ID / ADZUNA_API_KEY in backend/.env"

    what_query = role.strip()

    params = {
        "app_id":           ADZUNA_APP_ID,
        "app_key":          ADZUNA_API_KEY,
        "what":             what_query,
        "results_per_page": max(10, n),
        "sort_by":          "date",
        "content-type":     "application/json",
    }
    if location.strip():
        params["where"] = location.strip()

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 401:
            return [], "Adzuna auth failed (401). Verify ADZUNA_APP_ID and ADZUNA_API_KEY."
        if r.status_code == 403:
            return [], "Adzuna access denied (403). Check account access/region limits."
        if r.status_code == 429:
            return [], "Adzuna rate limit hit (429). Retry after a short delay."
        if r.status_code != 200:
            return [], f"Adzuna API error {r.status_code}: {r.text[:200]}"
        data = r.json()
        results = data.get("results", [])

        # Experience-level filtering after fetch (less restrictive than query stuffing).
        if exp_level == "Fresher":
            pos = ["intern", "internship", "trainee", "entry", "junior", "graduate", "fresher", "0-1", "0 to 1"]
            neg = ["senior", "lead", "principal", "manager", "architect", "staff", "2+ years", "3+ years", "5+ years"]
            filtered = []
            for j in results:
                txt = f"{j.get('title','')} {j.get('description','')}".lower()
                if any(p in txt for p in pos) and not any(x in txt for x in neg):
                    filtered.append(j)
            results = filtered or results

        return results[:n], None
    except requests.exceptions.ConnectionError as e:
        return [], f"Network error — could not reach Adzuna API. Check your internet connection. ({e})"
    except requests.exceptions.Timeout:
        return [], "Adzuna API timed out. Try again."
    except Exception as e:
        return [], f"Unexpected error: {e}"


def fetch_career_page_jobs(query: str, location: str, max_total: int = 40) -> list:
    """Fetch jobs from company career pages using JobRadar from job_alerts.py."""
    q = (query or "").strip()
    if not q:
        return []
    try:
        jr = JobRadar(verbose=False, max_per_company=4, delay=0.2)
        jobs = jr.search_jobs(q, companies=None, max_total=max_total)
        results = []
        for j in jobs:
            desc = getattr(j, "description", "") or ""
            results.append({
                "source": "Career Page",
                "title": getattr(j, "title", "N/A"),
                "company": getattr(j, "company", "N/A"),
                "location": getattr(j, "location", location or "N/A"),
                "description": desc[:300],
                "url": getattr(j, "apply_url", "#"),
            })
        return results
    except Exception:
        return []


def _career_link_is_valid(url: str, timeout: int = 8) -> bool:
    """Return True when URL is reachable and not a 404."""
    link = (url or "").strip()
    if not link or link == "#":
        return False
    try:
        h = requests.head(link, allow_redirects=True, timeout=timeout, headers=SCRAPE_HEADERS)
        if h.status_code == 404:
            return False
        if 200 <= h.status_code < 400:
            return True
        # Some career pages block HEAD; retry with GET.
        if h.status_code in (403, 405, 429) or h.status_code >= 500:
            g = requests.get(link, allow_redirects=True, timeout=timeout, headers=SCRAPE_HEADERS, stream=True)
            g.close()
            return g.status_code != 404
        return h.status_code != 404
    except requests.RequestException:
        return False


def filter_verified_career_jobs(jobs: list, max_workers: int = 10) -> list:
    """Keep only career jobs whose apply links are verified as non-404."""
    if not jobs:
        return []
    verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_career_link_is_valid, j.get("url", "")): j for j in jobs}
        for future in concurrent.futures.as_completed(future_map):
            item = future_map[future]
            try:
                if future.result():
                    verified.append(item)
            except Exception:
                continue
    return verified


def masked_key(value: str, visible: int = 4) -> str:
    if not value:
        return "(missing)"
    if len(value) <= visible * 2:
        return value[0] + ("*" * max(0, len(value) - 2)) + value[-1]
    return f"{value[:visible]}...{value[-visible:]}"


def get_relevant_portals(domains: list, skills: list, limit: int = 8) -> list:
    """Pick portals from portal.json relevant to user's domains/skills using partial matching."""
    wanted_fragments = set()
    for d in domains:
        for company in DOMAIN_TO_COMPANIES.get(d, []):
            wanted_fragments.add(company.lower())
    if not wanted_fragments:
        for companies in DOMAIN_TO_COMPANIES.values():
            for c in companies:
                wanted_fragments.add(c.lower())

    matched, seen = [], set()
    for p in PORTALS:
        pt = p["title"].lower()
        for frag in wanted_fragments:
            if frag in pt or pt in frag:
                if pt not in seen:
                    matched.append(p); seen.add(pt)
                break
        if len(matched) >= limit:
            break
    for p in PORTALS:
        if len(matched) >= limit:
            break
        if p["title"].lower() not in seen:
            matched.append(p); seen.add(p["title"].lower())
    return matched[:limit]


# ─── CAREER PAGE SCRAPER ──────────────────────────────────────────────────────
SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Known job-board URL patterns — scrape search results directly
JOB_BOARD_SEARCH = {
    "linkedin":    "https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}",
    "naukri":      "https://www.naukri.com/{query}-jobs-in-{loc}",
    "indeed":      "https://in.indeed.com/jobs?q={query}&l={loc}",
    "internshala": "https://internshala.com/internships/{query}-internship/",
    "shine":       "https://www.shine.com/job-search/{query}-jobs",
}

# CSS selectors that reliably identify job cards across popular sites
JOB_SELECTORS = [
    # Generic patterns
    {"card": "[class*='job-card']",   "title": "[class*='title']",   "link": "a"},
    {"card": "[class*='job-item']",   "title": "[class*='title']",   "link": "a"},
    {"card": "[class*='job-listing']","title": "h2,h3,h4",           "link": "a"},
    {"card": "[class*='position']",   "title": "h2,h3,h4",           "link": "a"},
    {"card": "[class*='opening']",    "title": "h2,h3,h4",           "link": "a"},
    {"card": "[class*='role']",       "title": "h2,h3,h4",           "link": "a"},
    {"card": "li[class*='job']",      "title": "h2,h3,h4,span,a",    "link": "a"},
    {"card": "tr[class*='job']",      "title": "td",                 "link": "a"},
    # Workday / Greenhouse / Lever patterns
    {"card": "[data-automation-id='jobTitle']", "title": "self",     "link": "a"},
    {"card": ".posting",              "title": "h5,.posting-title",  "link": "a[href]"},
    {"card": ".job",                  "title": "h3,h4,.job-title",   "link": "a"},
]

ROLE_KEYWORDS = [
    "engineer","developer","analyst","scientist","architect","lead","manager",
    "intern","trainee","associate","consultant","specialist","designer","researcher",
    "devops","mlops","qa","tester","sre","dba","administrator",
]


def _is_job_title(text: str) -> bool:
    """Heuristic: does this text look like a job title?"""
    t = text.lower().strip()
    if len(t) < 4 or len(t) > 120:
        return False
    return any(kw in t for kw in ROLE_KEYWORDS)


def _scrape_one_portal(portal: dict, search_terms: list, timeout: int = 8) -> list:
    """
    Scrape a single career page for job listings matching search_terms.
    Returns list of {title, company, url, description, source}.
    """
    company  = portal["title"]
    base_url = portal["link"]
    jobs     = []

    try:
        r = requests.get(base_url, headers=SCRAPE_HEADERS, timeout=timeout,
                         allow_redirects=True)
        if r.status_code not in (200, 201):
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        # ── Strategy 1: CSS selector patterns ─────────────────────────────────
        for sel in JOB_SELECTORS:
            cards = soup.select(sel["card"])
            if not cards:
                continue
            for card in cards[:30]:
                # Title
                if sel["title"] == "self":
                    title_el = card
                else:
                    title_el = card.select_one(sel["title"])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not _is_job_title(title):
                    continue

                # Link
                link_el = card.select_one(sel["link"]) if sel["link"] != "a" else card.find("a")
                href = ""
                if link_el and link_el.get("href"):
                    href = link_el["href"]
                    if href.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(base_url)
                        href = f"{parsed.scheme}://{parsed.netloc}{href}"
                    elif not href.startswith("http"):
                        href = base_url.rstrip("/") + "/" + href

                jobs.append({
                    "source":      f"Career Page",
                    "company":     company,
                    "title":       title,
                    "location":    "Check career page",
                    "description": card.get_text(separator=" ", strip=True)[:200],
                    "url":         href or base_url,
                    "salary":      None,
                })
            if jobs:
                break  # found cards with this selector, stop trying others

        # ── Strategy 2: Fallback — find all <a> tags that look like job links ─
        if not jobs:
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                if not _is_job_title(text):
                    continue
                href = a["href"]
                if href.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                elif not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href
                jobs.append({
                    "source":      "Career Page",
                    "company":     company,
                    "title":       text,
                    "location":    "Check career page",
                    "description": "",
                    "url":         href,
                    "salary":      None,
                })
            # Deduplicate by title
            seen_t = set()
            deduped = []
            for j in jobs:
                if j["title"] not in seen_t:
                    seen_t.add(j["title"]); deduped.append(j)
            jobs = deduped

    except Exception:
        pass

    # Filter to only jobs that match at least one search term
    if jobs and search_terms:
        terms_lower = [t.lower() for t in search_terms]
        filtered = [
            j for j in jobs
            if any(term in j["title"].lower() for term in terms_lower)
            or any(kw in j["title"].lower() for kw in ROLE_KEYWORDS)
        ]
        jobs = filtered if filtered else jobs[:3]  # fallback: return first 3

    return jobs[:5]  # max 5 per company


def scrape_portal_jobs(portals: list, search_terms: list, max_workers: int = 6) -> list:
    """
    Scrape multiple career pages in parallel using thread pool.
    Returns combined list of job dicts.
    """
    all_jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_scrape_one_portal, p, search_terms): p
            for p in portals
        }
        for future in concurrent.futures.as_completed(futures, timeout=20):
            try:
                result = future.result()
                all_jobs.extend(result)
            except Exception:
                pass
    return all_jobs


# ─── EMAIL ────────────────────────────────────────────────────────────────────
def build_email_html(jobs: list, portals: list, skills: list, exp_level: str) -> str:
    jobs_html = ""
    for j in jobs[:10]:
        tag_col  = "#7c6fff" if j.get("source") == "Adzuna" else "#ff6b8a"
        tag_lbl  = j.get("source", "Adzuna")
        sal      = f"💰 ₹{int(j['salary']):,}" if j.get("salary") else ""
        jobs_html += f"""
<div style="background:#f8f8ff;border-left:4px solid {tag_col};border-radius:6px;
            padding:14px 16px;margin:10px 0;">
  <span style="background:{tag_col};color:white;font-size:10px;padding:2px 8px;
               border-radius:10px;">{tag_lbl}</span>
  <h3 style="margin:5px 0 3px;color:#1a1a2e;font-size:15px;">{j.get('title','N/A')}</h3>
  <p style="margin:2px 0;color:#555;font-size:13px;">
    🏢 {j.get('company','N/A')} &nbsp;|&nbsp; 📍 {j.get('location','N/A')}
    {(' &nbsp;|&nbsp; ' + sal) if sal else ''}
  </p>
  <p style="margin:6px 0 0;font-size:12px;color:#888;">{j.get('description','')[:200]}...</p>
  <a href="{j.get('url','#')}" style="display:inline-block;margin-top:8px;background:{tag_col};
     color:white;text-decoration:none;padding:5px 14px;border-radius:4px;font-size:12px;">
    Apply Now →
  </a>
</div>"""

    portal_chips = "".join(
        f'<a href="{p["link"]}" style="display:inline-block;background:#f0eeff;color:#7c6fff;'
        f'padding:5px 12px;border-radius:20px;margin:4px;font-size:12px;text-decoration:none;">'
        f'🏢 {p["title"]}</a>'
        for p in portals[:10]
    )

    portals_section = ""
    if portal_chips:
        portals_section = f"""
    <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
    <h2 style="font-size:16px;color:#1a1a2e;">🏢 Company Career Portals</h2>
    {portal_chips}"""

    return f"""
<html><body style="font-family:'Segoe UI',sans-serif;max-width:640px;margin:0 auto;color:#333;">
  <div style="background:linear-gradient(135deg,#7c6fff,#ff6b8a);padding:28px;
              border-radius:12px 12px 0 0;text-align:center;">
    <h1 style="color:white;margin:0;font-size:22px;">🚀 Your Job Alert</h1>
    <p style="color:rgba(255,255,255,.85);margin:6px 0 0;font-size:14px;">
      {len(jobs)} openings &nbsp;|&nbsp; Level: <b>{exp_level}</b>
    </p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;border:1px solid #eee;">
    <p style="color:#666;font-size:13px;">Skills: <b>{', '.join(skills[:8])}</b></p>
    <h2 style="font-size:16px;color:#1a1a2e;">📋 Live Job Openings</h2>
    {jobs_html}
    {portals_section}
    <p style="color:#aaa;font-size:11px;text-align:center;margin-top:20px;">
      AI Smart Job Alert · {datetime.now().strftime('%B %d, %Y %H:%M')}
    </p>
  </div>
</body></html>"""


def send_email(sender, password, recipient, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html"))
    
    if SMTP_PORT == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as s:
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())


def schedule_daily_email(sender, password, recipient, html_fn, hour, minute):
    def _run():
        while True:
            now    = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            time.sleep((target - now).total_seconds())
            try:
                send_email(sender, password, recipient,
                           f"🚀 Daily Job Alert — {datetime.now().strftime('%b %d')}", html_fn())
            except Exception as ex:
                print(f"[Scheduler] {ex}")
    threading.Thread(target=_run, daemon=True).start()


# ─── ATS RESUME PDF ───────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def generate_ats_resume_json(resume_text, jd, name):
    prompt = f"""
You are an ATS resume expert.
RESUME: {resume_text[:3000]}
JOB DESCRIPTION: {jd[:2000]}
NAME: {name}

Generate a fully ATS-optimised resume as JSON ONLY (no markdown):
{{"name":"","title":"","email":"","phone":"","location":"","linkedin":"",
"summary":"","skills":[],"experience":[{{"company":"","role":"","duration":"","bullets":[]}}],
"education":[{{"degree":"","institution":"","year":"","gpa":""}}],
"projects":[{{"name":"","description":"","impact":""}}],"certifications":[]}}
"""
    return gemini_generate(prompt)


def build_resume_pdf(d):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=.6*inch, rightMargin=.6*inch,
        topMargin=.6*inch, bottomMargin=.6*inch)
    acc  = colors.HexColor("#7c6fff")
    dk   = colors.HexColor("#1a1a2e")
    gray = colors.HexColor("#555")
    lg   = colors.HexColor("#ddd")
    N  = ParagraphStyle("N",  fontName="Helvetica-Bold", fontSize=20, textColor=dk,    spaceAfter=2,  alignment=TA_CENTER)
    T  = ParagraphStyle("T",  fontName="Helvetica",      fontSize=11, textColor=acc,   spaceAfter=4,  alignment=TA_CENTER)
    C  = ParagraphStyle("C",  fontName="Helvetica",      fontSize=8,  textColor=gray,  spaceAfter=8,  alignment=TA_CENTER)
    SH = ParagraphStyle("SH", fontName="Helvetica-Bold", fontSize=10, textColor=acc,   spaceBefore=10,spaceAfter=3)
    BD = ParagraphStyle("BD", fontName="Helvetica",      fontSize=9,  textColor=colors.HexColor("#222"),spaceAfter=2,leading=13)
    BU = ParagraphStyle("BU", fontName="Helvetica",      fontSize=9,  textColor=colors.HexColor("#333"),spaceAfter=1,leading=12,leftIndent=12)
    BL = ParagraphStyle("BL", fontName="Helvetica-Bold", fontSize=9,  textColor=dk,    spaceAfter=1)
    IT = ParagraphStyle("IT", fontName="Helvetica-Oblique",fontSize=8.5,textColor=gray,spaceAfter=2)
    s  = []
    hr = lambda: HRFlowable(width="100%", thickness=0.5, color=lg,  spaceAfter=4)
    shr= lambda: HRFlowable(width="100%", thickness=1,   color=acc, spaceAfter=6)
    def sec(t): s.append(Paragraph(t,SH)); s.append(hr())
    s += [Paragraph(d.get("name",""),N), Paragraph(d.get("title",""),T)]
    s += [Paragraph("  |  ".join(x for x in [d.get("email"),d.get("phone"),d.get("location"),d.get("linkedin")] if x),C)]
    s.append(shr())
    if d.get("summary"):    sec("PROFESSIONAL SUMMARY"); s.append(Paragraph(d["summary"],BD))
    if d.get("skills"):     sec("TECHNICAL SKILLS");     s.append(Paragraph("  •  ".join(d["skills"]),BD))
    if d.get("experience"):
        sec("EXPERIENCE")
        for e in d["experience"]:
            s += [Paragraph(f"{e.get('role','')} — {e.get('company','')}",BL),
                  Paragraph(e.get("duration",""),IT)]
            for b in e.get("bullets",[]): s.append(Paragraph(f"• {b}",BU))
            s.append(Spacer(1,4))
    if d.get("education"):
        sec("EDUCATION")
        for e in d["education"]:
            gpa = f" | GPA: {e['gpa']}" if e.get("gpa") else ""
            s.append(Paragraph(f"{e.get('degree','')} — {e.get('institution','')}{gpa} ({e.get('year','')})",BD))
    if d.get("projects"):
        sec("PROJECTS")
        for p in d["projects"]:
            s += [Paragraph(p.get("name",""),BL), Paragraph(p.get("description",""),BU)]
            if p.get("impact"): s.append(Paragraph(f"📈 {p['impact']}",BU))
            s.append(Spacer(1,3))
    if d.get("certifications"):
        sec("CERTIFICATIONS")
        for c in d["certifications"]: s.append(Paragraph(f"• {c}",BU))
    doc.build(s)
    return buf.getvalue()


def safe_json(text):
    try:
        return json.loads(re.sub(r"```(?:json)?|```","",text).strip())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR  (P3: email config removed — only country + schedule here)
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="mono grad-text" style="font-size:1.1rem;font-weight:700;">⚙️ Settings</div>',
                unsafe_allow_html=True)
    st.divider()
    st.markdown("**🌍 Job Market**")
    country_map  = {"India":"in","USA":"us","UK":"gb","Canada":"ca","Australia":"au"}
    country_name = st.selectbox("Country", list(country_map.keys()))
    country_code = country_map[country_name]
    st.divider()
    st.markdown("**⏰ Daily Alert Time**")
    c1, c2     = st.columns(2)
    daily_hour = c1.number_input("Hour (24h)", 0, 23, 8)
    daily_min  = c2.number_input("Min",        0, 59, 0)
    st.caption(f"Fires daily at {daily_hour:02d}:{daily_min:02d}")
    st.divider()
    st.caption(f"📋 {len(PORTALS)} portals loaded")
    st.caption("AI Smart Job System v5.0")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<h1 class="grad-text" style="font-size:2rem;margin-bottom:.1rem;">🚀 AI Smart Job Alert System</h1>',
            unsafe_allow_html=True)
st.markdown('<div style="color:var(--muted);font-size:.88rem;margin-bottom:1.5rem;">'
            'Upload Resume → NLP Parsing → Smart Job Fetch → Direct Apply → Email Alerts → ATS Resume'
            '</div>', unsafe_allow_html=True)

# Session-state init
for _k in ["fhash","resume_text","info","search_results","portal_jobs","portal_matches",
           "search_role","search_exp","ats_data","ats_pdf","scheduler_key","roles_output","roles_table_rows"]:
    if _k not in st.session_state:
        st.session_state[_k] = None

uploaded = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])

if uploaded:
    file_bytes = uploaded.read()
    fhash      = hashlib.md5(file_bytes).hexdigest()

    if st.session_state.get("fhash") != fhash:
        st.session_state.fhash = fhash
        with st.spinner("📄 Parsing resume with NLP..."):
            resume_text = parse_resume_bytes(file_bytes)
            info        = extract_info_from_resume(resume_text)
        st.session_state.resume_text = resume_text
        st.session_state.info        = info
        with st.spinner("Analyzing job roles and ATS scores..."):
            roles_output = infer_roles_and_ats(info.get("skills", []))
        st.session_state.roles_output = roles_output
        st.session_state.roles_table_rows = roles_output_to_rows(roles_output)
        st.markdown('<div class="success-box">✅ Resume parsed successfully!</div>',
                    unsafe_allow_html=True)
    else:
        resume_text = st.session_state.get("resume_text", "")
        info        = st.session_state.get("info", {})
        if not st.session_state.get("roles_output"):
            with st.spinner("Analyzing job roles and ATS scores..."):
                roles_output = infer_roles_and_ats(info.get("skills", []))
            st.session_state.roles_output = roles_output
            st.session_state.roles_table_rows = roles_output_to_rows(roles_output)

    skills   = info.get("skills", [])
    domains  = info.get("domains", [])
    det_exp  = info.get("experience_level", "Fresher")
    det_loc  = info.get("location", "")
    det_name = info.get("name", "")

    # ── Profile strip ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [
        (c1, len(skills),                         "Skills Detected"),
        (c2, info.get("projects_count", 0),        "Projects"),
        (c3, info.get("experience_years", "—"),    "Exp Years"),
        (c4, det_exp,                               "Detected Level"),
    ]:
        fs = "font-size:.95rem;" if isinstance(num, str) else ""
        col.markdown(
            f'<div class="metric-box"><div class="metric-num" style="{fs}">{num}</div>'
            f'<div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown("".join(f'<span class="badge">{s}</span>' for s in skills),
                unsafe_allow_html=True)
    if info.get("experience_signals"):
        st.markdown(
            f'<div class="info-box">📊 <b>Experience signal:</b> {info["experience_signals"]}</div>',
            unsafe_allow_html=True)
    st.markdown('<hr class="thin">', unsafe_allow_html=True)

    # ===== Role + ATS (auto, no button) =====
    st.subheader("📊 Recommended Job Roles")
    role_rows = st.session_state.get("roles_table_rows") or []
    if role_rows:
        st.markdown(build_roles_markdown_table(role_rows))
    elif st.session_state.get("roles_output"):
        st.markdown(st.session_state.roles_output)
    else:
        st.info("Role recommendations will appear after resume parsing.")
    st.info("ATS Score indicates how suitable your resume is for each role.")

    # ── TABS — P2: only 2 tabs now (portals tab removed) ──────────────────────
    tab1, tab2, tab3 = st.tabs(["🔎 Smart Job Search", "📧 Email Alerts", "📄 ATS Resume Builder"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SMART JOB SEARCH
    # P1: fetch from Adzuna + portal.json career pages.
    # Auto-suggest roles from resume if query blank.
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 🔎 Smart Job Search")
        st.markdown(
            '<div class="info-box">Type a role/skill OR leave blank — '
            'auto-matches jobs from your resume skills. Results include live '
            'Adzuna listings <b>and</b> direct company career page links.</div>',
            unsafe_allow_html=True)

        suggested_roles = suggest_roles_from_skills(skills, domains)
        if suggested_roles:
            st.markdown("**Suggested roles from extracted skills:**")
            st.markdown("".join(f'<span class=\"badge\">{r}</span>' for r in suggested_roles[:8]),
                        unsafe_allow_html=True)

        ca, cb, cc = st.columns([3, 2, 2])
        user_query  = ca.text_input("Role / Keyword (optional)",
                                    placeholder="e.g. AI, NLP, data analyst, backend")
        role_pick   = ca.selectbox("Or pick a suggested role", [""] + suggested_roles[:8])
        exp_options = ["Auto (from Resume)"] + list(EXP_BUCKETS.keys())
        exp_choice  = cb.selectbox("Experience Level", exp_options)
        loc_input   = cc.text_input("📍 Location", value=det_loc,
                                    placeholder="e.g. Bangalore, Hyderabad")

        if st.button("🚀 Search Jobs"):
            exp_level = det_exp if exp_choice == "Auto (from Resume)" else exp_choice

            # ── Decide search terms ────────────────────────────────────────────
            effective_query = user_query.strip() or role_pick.strip()
            if effective_query:
                with st.spinner("🧠 AI expanding keyword..."):
                    search_terms = expand_keywords_ai(effective_query, tuple(skills))
                st.markdown('<div class="info-box">🧠 AI expanded your keyword into precise search terms.</div>',
                            unsafe_allow_html=True)
            else:
                search_terms = suggest_roles_from_skills(skills, domains)
                if not search_terms:
                    search_terms = ["Software Engineer"]
                st.markdown('<div class="info-box">ℹ️ No keyword entered — '
                            'auto-suggesting roles from your resume skills.</div>',
                            unsafe_allow_html=True)

            st.markdown("**🎯 Searching for:**")
            st.markdown("".join(f'<span class="badge">{t}</span>' for t in search_terms),
                        unsafe_allow_html=True)
            st.markdown("")

            # ── Fetch Adzuna jobs ──────────────────────────────────────────────

            adzuna_results = []
            portal_jobs = []
            adzuna_error = None

            # Live Jobs tab: Adzuna API only.
            with st.spinner("Fetching live jobs from Adzuna API..."):
                seen_adzuna = set()
                for term in search_terms[:6]:
                    jobs, err = fetch_adzuna_jobs(term, country_code, exp_level, loc_input, n=8)
                    if err and not adzuna_error:
                        adzuna_error = err
                    for j in jobs:
                        url = j.get("redirect_url", "#")
                        key = (url or "").strip().lower() or f"{j.get('title','')}|{j.get('company', {}).get('display_name','')}"
                        if key in seen_adzuna:
                            continue
                        seen_adzuna.add(key)
                        adzuna_results.append({
                            "source": "Adzuna",
                            "title": j.get("title", "N/A"),
                            "company": j.get("company", {}).get("display_name", "N/A"),
                            "location": j.get("location", {}).get("display_name", "N/A"),
                            "description": (j.get("description") or "")[:300],
                            "url": url,
                            "salary": j.get("salary_min"),
                        })
                    if len(adzuna_results) >= 24:
                        break

            # Career Pages tab: JobRadar from job_alerts.py only.
            with st.spinner("Fetching jobs from company career pages (JobRadar)..."):
                seen_portal = set()
                for term in search_terms[:4]:
                    jobs = fetch_career_page_jobs(term, loc_input, max_total=30)
                    for item in jobs:
                        key = (item.get("url", "") or "").strip().lower() or f"{item.get('title','')}|{item.get('company','')}|{item.get('location','')}"
                        if key in seen_portal:
                            continue
                        seen_portal.add(key)
                        portal_jobs.append(item)
                    if len(portal_jobs) >= 36:
                        break

            # Keep fallback company cards when no parsed career jobs are available.
            portal_matches = get_relevant_portals(domains, skills, limit=10)

            # Fallback 1: if Adzuna is empty with location, retry without location.
            if not adzuna_results and loc_input.strip():
                for term in search_terms[:6]:
                    jobs, err = fetch_adzuna_jobs(term, country_code, exp_level, "", n=5)
                    if err and not adzuna_error:
                        adzuna_error = err
                    for j in jobs:
                        adzuna_results.append({
                            "source": "Adzuna",
                            "title": j.get("title", "N/A"),
                            "company": j.get("company", {}).get("display_name", "N/A"),
                            "location": j.get("location", {}).get("display_name", "N/A"),
                            "description": (j.get("description") or "")[:300],
                            "url": j.get("redirect_url", "#"),
                            "salary": j.get("salary_min"),
                        })
                    if adzuna_results:
                        break

            # Fallback 2: if career-page jobs are empty from combined flow, scrape directly.
            if not portal_jobs and portal_matches:
                with st.spinner(f"Scraping {len(portal_matches)} company career pages..."):
                    portal_jobs = scrape_portal_jobs(portal_matches, search_terms)

            # Verify apply links and remove broken career-page URLs before display.
            if portal_jobs:
                with st.spinner("Verifying career page apply links..."):
                    portal_jobs = filter_verified_career_jobs(portal_jobs, max_workers=10)

            # Store everything
            st.session_state.search_results  = adzuna_results
            st.session_state.portal_jobs     = portal_jobs
            st.session_state.portal_matches  = portal_matches
            st.session_state.adzuna_error    = adzuna_error
            st.session_state.search_role     = user_query.strip() or ", ".join(search_terms[:3])
            st.session_state.search_exp      = exp_level


        # ── Display results ────────────────────────────────────────────────────
        if st.session_state.get("search_results") is not None:
            adzuna_results = st.session_state.get("search_results", [])
            portal_jobs    = st.session_state.get("portal_jobs", [])
            portal_matches = st.session_state.get("portal_matches", [])
            adzuna_error   = st.session_state.get("adzuna_error")

            total_jobs = len(adzuna_results) + len(portal_jobs)
            st.markdown(
                f'<div class="success-box">✅ <b>{len(adzuna_results)}</b> live Adzuna jobs  '
                f'+ <b>{len(portal_jobs)}</b> jobs from career pages  '
                f'({len(portal_matches)} companies scraped)</div>',
                unsafe_allow_html=True)

            # ── Tab display: Adzuna | Career Pages ────────────────────────────
            res_tab1, res_tab2 = st.tabs([
                f"📋 Live Jobs ({len(adzuna_results)})",
                f"🏢 From Career Pages ({len(portal_jobs)})"
            ])

            with res_tab1:
                if adzuna_results:
                    for job in adzuna_results:
                        sal_str = f"💰 ₹{int(job['salary']):,}" if job.get("salary") else ""
                        st.markdown(f"""
<div class="card card-l">
  <span class="tag tag-live">Live · Adzuna</span>
  <div class="mono" style="font-size:.92rem;color:var(--text);font-weight:700;margin-top:4px;">
    {job['title']}
  </div>
  <div style="font-size:.82rem;color:var(--muted);margin:4px 0;">
    🏢 {job['company']} &nbsp;|&nbsp; 📍 {job['location']}
    {(' &nbsp;|&nbsp; ' + sal_str) if sal_str else ''}
  </div>
  <div style="font-size:.8rem;color:#aaaacc;margin:5px 0 8px;">{job['description']}...</div>
  <a href="{job['url']}" target="_blank" class="apply-btn">Apply Now →</a>
</div>""", unsafe_allow_html=True)
                else:
                    st.markdown('<div class="warn-box">⚠️ No live Adzuna jobs found. '
                                'Check API credentials or try a different keyword/location.</div>',
                                unsafe_allow_html=True)
                    st.info("💡 Get free Adzuna API credentials at https://developer.adzuna.com")

            with res_tab2:
                if portal_jobs:
                    st.markdown(f"Found **{len(portal_jobs)}** job listings scraped directly "
                                f"from company career pages:")
                    for job in portal_jobs:
                        st.markdown(f"""
<div class="card card-p">
  <span class="tag tag-portal">Career Page · {job['company']}</span>
  <div class="mono" style="font-size:.9rem;color:var(--text);font-weight:700;margin-top:4px;">
    {job['title']}
  </div>
  <div style="font-size:.82rem;color:var(--muted);margin:4px 0;">
    🏢 {job['company']} &nbsp;|&nbsp; 📍 {job['location']}
  </div>
  {f'<div style="font-size:.8rem;color:#aaaacc;margin:5px 0 6px;">{job["description"]}...</div>' if job.get("description") else ''}
  <a href="{job['url']}" target="_blank" class="portal-btn">Apply Directly →</a>
</div>""", unsafe_allow_html=True)
                else:
                    # Career pages scraped but no structured job listings extracted
                    # Show them as direct visit links instead
                    st.markdown('<div class="warn-box">ℹ️ Could not extract structured job listings '
                                'from career pages (many use JavaScript rendering). '
                                'Visit them directly below:</div>', unsafe_allow_html=True)
                    if portal_matches:
                        cols = st.columns(2)
                        for i, p in enumerate(portal_matches):
                            with cols[i % 2]:
                                st.markdown(f"""
<div class="card card-p" style="padding:.9rem 1.1rem;">
  <div style="font-size:.9rem;color:var(--text);font-weight:600;margin-bottom:5px;">
    🏢 {p['title']}
  </div>
  <div style="font-size:.78rem;color:var(--muted);margin-bottom:8px;">
    Apply directly for roles matching your skills
  </div>
  <a href="{p['link']}" target="_blank" class="portal-btn">Visit Careers →</a>
</div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — EMAIL ALERTS
    # P3: email config collected inline here, not in sidebar
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 📧 Email Job Alerts")
        st.markdown('<div class="info-box">Configure your email below and get instant or '
                    'daily job alerts directly to your inbox — with live jobs + career page links.</div>',
                    unsafe_allow_html=True)

        # ── Inline email config (P3 fix) ──────────────────────────────────────
        with st.expander("🔐 Email Configuration", expanded=True):
            ec1, ec2       = st.columns(2)
            sender_email    = ec1.text_input("Your Email", value=SMTP_USER_ENV, placeholder="you@gmail.com", key="s_email")
            sender_password = ec2.text_input("App Password", value=SMTP_PASS_ENV, type="password",
                                             help="App Password / Email Password", key="s_pw")
            recipient_email = st.text_input("Send Alert To", value=SMTP_USER_ENV, placeholder="recipient@example.com", key="s_recv")
            st.caption(f"Using SMTP Server: `{SMTP_SERVER}:{SMTP_PORT}`. Configure in .env if needed.")

        email_ok = bool(sender_email and sender_password and recipient_email)
        st.markdown('<hr class="thin">', unsafe_allow_html=True)

        # Alert config
        alert_role = st.text_input("Role for alert",
                                   value=st.session_state.get("search_role") or "",
                                   placeholder="e.g. Data Scientist, ML Engineer")
        exp_list  = list(EXP_BUCKETS.keys())
        alert_exp = st.selectbox("Experience Level for Alert", exp_list,
                                 index=exp_list.index(det_exp) if det_exp in exp_list else 0)
        alert_loc = st.text_input("Location for Alert", value=det_loc,
                                  placeholder="e.g. Hyderabad, Bangalore")

        def _build_alert_html():
            terms    = expand_keywords_ai(alert_role, tuple(skills)) if alert_role.strip() \
                       else suggest_roles_from_skills(skills, domains) or ["Software Engineer"]
            all_jobs = []
            seen     = set()
            # Adzuna jobs
            for t in terms[:4]:
                jobs, _ = fetch_adzuna_jobs(t, country_code, alert_exp, alert_loc, n=4)
                for j in jobs:
                    jid = j.get("id", "")
                    if jid and jid not in seen:
                        seen.add(jid)
                        all_jobs.append({
                            "source":      "Adzuna",
                            "title":       j.get("title", "N/A"),
                            "company":     j.get("company", {}).get("display_name", "N/A"),
                            "location":    j.get("location", {}).get("display_name", "N/A"),
                            "description": (j.get("description") or "")[:200],
                            "url":         j.get("redirect_url", "#"),
                            "salary":      j.get("salary_min"),
                        })
            # Career page scraped jobs
            portals_for_email = get_relevant_portals(domains, skills, limit=6)
            scraped = scrape_portal_jobs(portals_for_email, terms)
            all_jobs.extend(scraped)
            return build_email_html(all_jobs, portals_for_email, skills, alert_exp)

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### ⚡ Instant Alert")
            st.caption("Click → email sent immediately")
            if st.button("📬 Send Now"):
                if not email_ok:
                    st.warning("Fill in the email configuration above first.")
                else:
                    try:
                        with st.spinner("Fetching jobs & sending email..."):
                            # Use cached results if available to ensure email matches UI
                            cached_jobs = (st.session_state.get("search_results") or []) + \
                                          (st.session_state.get("portal_jobs") or [])
                            
                            if cached_jobs:
                                portals_for_email = st.session_state.get("portal_matches") or \
                                                    get_relevant_portals(domains, skills, limit=6)
                                html = build_email_html(cached_jobs, portals_for_email, skills, alert_exp)
                            else:
                                html = _build_alert_html()

                            send_email(sender_email, sender_password, recipient_email,
                                       f"🚀 Job Alert: {alert_role or 'Resume Match'} — "
                                       f"{datetime.now().strftime('%b %d, %Y')}", html)
                        st.markdown('<div class="success-box">✅ Email sent successfully!</div>',
                                    unsafe_allow_html=True)
                    except smtplib.SMTPAuthenticationError:
                        st.error("❌ Auth failed. Use a Gmail App Password "
                                 "(Google → Security → App Passwords).")
                    except Exception as e:
                        st.error(f"❌ {e}")

        with col_b:
            st.markdown("#### ⏰ Daily Scheduler")
            st.caption(f"Fires automatically every day at {daily_hour:02d}:{daily_min:02d}")
            skey       = f"sched_{daily_hour}_{daily_min}_{sender_email}_{recipient_email}"
            is_running = st.session_state.get("scheduler_key") == skey

            if is_running:
                st.markdown('<div class="success-box">✅ Daily alert is <b>active</b>!</div>',
                            unsafe_allow_html=True)
                if st.button("🛑 Stop Scheduler"):
                    st.session_state.scheduler_key = None
                    st.info("Will stop on next app restart.")
            else:
                if st.button("▶️ Start Daily Scheduler"):
                    if not email_ok:
                        st.warning("Fill in the email configuration above first.")
                    else:
                        schedule_daily_email(sender_email, sender_password, recipient_email,
                                             _build_alert_html, daily_hour, daily_min)
                        st.session_state.scheduler_key = skey
                        st.markdown(
                            f'<div class="success-box">✅ Scheduler started! '
                            f'Daily alert at {daily_hour:02d}:{daily_min:02d}</div>',
                            unsafe_allow_html=True)
                        st.markdown('<div class="warn-box">⚠️ Keep the app running '
                                    'for the scheduler to fire.</div>', unsafe_allow_html=True)

        st.markdown('<hr class="thin">', unsafe_allow_html=True)
        if st.button("👁️ Preview Email"):
            with st.spinner("Building email preview..."):
                html = _build_alert_html()
            st.components.v1.html(html, height=650, scrolling=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — ATS RESUME BUILDER
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 📄 ATS Resume Builder")
        st.markdown('<div class="info-box">Paste a job description → AI rewrites your resume '
                    'to match it → Download ATS-optimised PDF.</div>', unsafe_allow_html=True)

        builder_name = st.text_input("Your Full Name", value=det_name, placeholder="e.g. Ravi Kumar")
        builder_jd   = st.text_area("Target Job Description", height=200,
                                    placeholder="Paste the full job description here...")

        if st.button("⚡ Generate ATS Resume PDF"):
            if not builder_jd.strip():
                st.warning("Paste a job description first.")
            elif not builder_name.strip():
                st.warning("Enter your name.")
            else:
                with st.spinner("AI building ATS-optimised resume..."):
                    raw  = generate_ats_resume_json(resume_text, builder_jd, builder_name)
                    data = safe_json(raw)
                if data:
                    st.session_state.ats_data = data
                    try:
                        pdf = build_resume_pdf(data)
                        st.session_state.ats_pdf = pdf
                        st.markdown('<div class="success-box">✅ Resume ready to download!</div>',
                                    unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"PDF error: {e}")
                else:
                    st.error("AI returned unexpected format. Try again.")
                    st.code(raw)

        if st.session_state.get("ats_pdf") and st.session_state.get("ats_data"):
            d = st.session_state.get("ats_data", {})
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-box"><div class="metric-num">'
                        f'{len(d.get("skills",[]))}</div><div class="metric-lbl">Skills</div></div>',
                        unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-box"><div class="metric-num">'
                        f'{len(d.get("experience",[]))}</div><div class="metric-lbl">Experience</div></div>',
                        unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-box"><div class="metric-num">'
                        f'{len(d.get("projects",[]))}</div><div class="metric-lbl">Projects</div></div>',
                        unsafe_allow_html=True)
            st.markdown(f"**Summary preview:** {d.get('summary','')[:200]}...")
            fname = f"ATS_Resume_{builder_name.replace(' ', '_')}.pdf"
            st.download_button("⬇️ Download ATS Resume PDF",
                               data=st.session_state.ats_pdf,
                               file_name=fname, mime="application/pdf")

else:
    st.markdown("""
<div style="text-align:center;padding:5rem 2rem;border:1px dashed var(--border);
            border-radius:16px;margin-top:2rem;">
  <div style="font-size:3.5rem;margin-bottom:1rem;">📄</div>
  <div class="mono grad-text" style="font-size:1.1rem;">Upload your resume PDF to get started</div>
  <div style="color:var(--muted);font-size:.85rem;margin-top:.6rem;">
    NLP skill extraction · Smart job search · Direct apply links · Email alerts · ATS resume builder
  </div>
</div>""", unsafe_allow_html=True)
