import streamlit as st
import os
import pdfplumber
import spacy
import requests
import google.genai as genai

# ================= CONFIG =================
api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyD5BKy8puMR1EIvGZtgJ2swCR1i7JYTJrU"
client = genai.Client(api_key=api_key)
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID") or "1c818aef"
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY") or "9c313ee332061bc409da3e8b8748208e"

nlp = spacy.load("en_core_web_sm")

st.set_page_config(
    page_title="AI Smart Job Recommendation System",
    layout="wide"
)

# ================= FUNCTIONS =================
@st.cache_data
def parse_resume(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

@st.cache_data
def extract_skills(resume_text):
    skills_db = [
        "python","java","sql","machine learning","deep learning","nlp",
        "data analysis","data engineering","backend","api","cloud",
        "aws","docker","kubernetes","cyber security","devops"
    ]
    doc = nlp(resume_text.lower())
    return list({token.text for token in doc if token.text in skills_db})

@st.cache_data
def infer_roles_and_ats(skills):
    if not client:
        return "API key not configured. Please set GEMINI_API_KEY in your environment."
    prompt = f"""
You are a technical recruiter.

Candidate skills:
{", ".join(skills)}

TASK:
Suggest 3–5 job roles for a fresher.
For each role:
- ATS match percentage (0–100)
- Short justification
- Missing skills

Format:
Role | ATS % | Reason | Missing Skills
"""
    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
    return response.text

@st.cache_data
def fetch_jobs(role):
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": role,
        "results_per_page": 5,
        "sort_by": "date"
    }
    return requests.get(url, params=params).json().get("results", [])

@st.cache_data
def optimize_resume(resume_text, jd):
    prompt = f"""
You are a Big-4 resume consultant.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd}

Provide:
- Persona shift
- Executive summary rewrite
- Project reframing
- Skills alignment
- ATS improvement suggestions
"""
    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
    return response.text

# ================= UI =================
st.title("🚀 AI-Based Smart Job Recommendation & ATS System")
st.markdown("Final Year Project | NLP + Gemini + Real-Time Jobs")

uploaded_file = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])

if uploaded_file:
    if uploaded_file != st.session_state.get("uploaded_file"):
        st.session_state.uploaded_file = uploaded_file
        with st.spinner("Parsing resume..."):
            resume_text = parse_resume(uploaded_file)
        st.session_state.resume_text = resume_text
        st.success("Resume parsed successfully")

        # ===== Skills =====
        with st.spinner("Extracting skills..."):
            skills = extract_skills(resume_text)
        st.session_state.skills = skills
    else:
        resume_text = st.session_state.get("resume_text")
        skills = st.session_state.get("skills")

    if skills:
        st.subheader("🔍 Extracted Skills")
        st.write(skills)

        # ===== Role + ATS =====
        if st.button("🎯 Analyze Job Roles & ATS Score"):
            st.subheader("📊 Recommended Job Roles")
            with st.spinner("Analyzing job roles and ATS scores..."):
                roles_output = infer_roles_and_ats(skills)
                st.session_state.roles_output = roles_output
                st.markdown(roles_output)
                st.info("ATS Score indicates how suitable your resume is for each role.")
        elif "roles_output" in st.session_state:
            st.subheader("📊 Recommended Job Roles")
            st.markdown(st.session_state.roles_output)
            st.info("ATS Score indicates how suitable your resume is for each role.")

        # ===== Live Jobs =====
        st.subheader("🌐 Live Job Openings")
        selected_role = st.text_input("Enter a Role (e.g., Data Engineer)")

        if st.button("🔎 Fetch Live Jobs"):
            with st.spinner("Fetching live jobs..."):
                jobs = fetch_jobs(selected_role)
                st.session_state.jobs = jobs
                for job in jobs:
                    st.markdown(f"### {job['title']}")
                    st.write("Company:", job["company"]["display_name"])
                    st.write("Location:", job["location"]["display_name"])
                    st.markdown(f"[Apply Here]({job['redirect_url']})")
                    st.progress(70)
                    st.divider()
        elif "jobs" in st.session_state:
            for job in st.session_state.jobs:
                st.markdown(f"### {job['title']}")
                st.write("Company:", job["company"]["display_name"])
                st.write("Location:", job["location"]["display_name"])
                st.markdown(f"[Apply Here]({job['redirect_url']})")
                st.progress(70)
                st.divider()

        # ===== JD Optimization =====
        st.subheader("✍️ Resume Optimization (JD-Based)")
        jd_text = st.text_area("Paste Job Description")

        if st.button("🧠 Suggest Resume Improvements"):
            with st.spinner("Optimizing resume..."):
                optimized = optimize_resume(resume_text, jd_text)
                st.session_state.optimized = optimized
                st.markdown(optimized)
        elif "optimized" in st.session_state:
            st.markdown(st.session_state.optimized)
