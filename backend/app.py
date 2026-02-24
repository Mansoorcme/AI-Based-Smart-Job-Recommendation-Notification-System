"""
app.py — Flask REST API for the AI Job Alert System.
Run from the backend/ folder:  python app.py

All module files (config.py, resume_parser.py, etc.) must be in the SAME folder as app.py.
"""

import hashlib
import json
import re
import os
import sys

# ── Ensure this folder is on sys.path so sibling modules are importable ──────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from io import BytesIO

# ── Direct imports — no dot prefix, no package ───────────────────────────────
from resume_parser import parse_pdf_bytes, extract_resume_info
from ai_roles      import (
    suggest_roles_from_skills, expand_keywords_ai,
    infer_roles_and_ats, parse_roles_output, build_roles_markdown_table,
)
from job_search    import (
    fetch_adzuna_jobs, fetch_career_page_jobs,
    fetch_aicte_internships, fetch_startup_jobs, filter_verified_career_jobs,
)
from portals       import load_portals, get_relevant_portals, scrape_portal_jobs
from email_alerts  import build_email_html, send_email
from ats_resume    import generate_ats_resume_json, build_resume_pdf, safe_parse_json
from config        import COUNTRY_MAP

# ── App setup ─────────────────────────────────────────────────────────────────
app     = Flask(__name__)
CORS(app)          # allow all origins — restrict to ["https://yourapp.com"] in production
PORTALS = load_portals()
print(f"[JobRadar] Loaded {len(PORTALS)} portals.")


# ── Tiny helpers ──────────────────────────────────────────────────────────────
def _body() -> dict:
    try:
        return request.get_json(force=True) or {}
    except Exception:
        return {}

def _ok(data: dict):
    return jsonify({"ok": True, **data})

def _err(msg: str, status: int = 400):
    return jsonify({"ok": False, "error": msg}), status


# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return _ok({"service": "JobRadar AI Backend", "version": "5.0", "portals": len(PORTALS)})


# ── Resume Parse ──────────────────────────────────────────────────────────────
@app.route("/api/resume/parse", methods=["POST"])
def resume_parse():
    if "resume" not in request.files:
        return _err("No 'resume' file in request.")
    file_bytes = request.files["resume"].read()
    if not file_bytes:
        return _err("Uploaded file is empty.")

    file_hash   = hashlib.md5(file_bytes).hexdigest()
    resume_text = parse_pdf_bytes(file_bytes)
    info        = extract_resume_info(resume_text)
    roles       = suggest_roles_from_skills(info.get("skills",[]), info.get("domains",[]))

    return _ok({"resume_text": resume_text, "info": info,
                "suggested_roles": roles, "file_hash": file_hash})


# ── ATS Role Analysis ─────────────────────────────────────────────────────────
@app.route("/api/resume/ats-roles", methods=["POST"])
def ats_roles():
    body   = _body()
    skills = body.get("skills", [])
    if not skills:
        return _err("'skills' array is required.")
    markdown   = infer_roles_and_ats(skills)
    table_rows = parse_roles_output(markdown)
    return _ok({"markdown": markdown, "table_rows": table_rows})


# ── Full Job Search ───────────────────────────────────────────────────────────
@app.route("/api/jobs/search", methods=["POST"])
def jobs_search():
    body      = _body()
    query     = body.get("query","").strip()
    skills    = body.get("skills",[])
    domains   = body.get("domains",[])
    exp_level = body.get("exp_level","Fresher")
    location  = body.get("location","")
    country   = COUNTRY_MAP.get(body.get("country","India"),"in")

    search_terms = (expand_keywords_ai(query, skills) if query
                    else suggest_roles_from_skills(skills, domains) or ["Software Engineer"])

    # Adzuna
    adzuna_jobs, adzuna_error, seen_az = [], None, set()
    for term in search_terms[:6]:
        jobs, err = fetch_adzuna_jobs(term, country, exp_level, location, n=8)
        if err and not adzuna_error:
            adzuna_error = err
        for j in jobs:
            key = (j.get("url") or "").strip().lower() or f"{j['title']}|{j['company']}"
            if key not in seen_az:
                seen_az.add(key); adzuna_jobs.append(j)
        if len(adzuna_jobs) >= 24:
            break

    # Retry without location if empty
    if not adzuna_jobs and location.strip():
        for term in search_terms[:4]:
            jobs, _ = fetch_adzuna_jobs(term, country, exp_level, "", n=5)
            adzuna_jobs.extend(jobs)
            if adzuna_jobs:
                break

    # Career pages
    career_jobs    = fetch_career_page_jobs(search_terms, location, max_total=36)
    portal_matches = get_relevant_portals(domains, skills, PORTALS, limit=10)

    if not career_jobs and portal_matches:
        career_jobs = scrape_portal_jobs(portal_matches, search_terms)
    if career_jobs:
        career_jobs = filter_verified_career_jobs(career_jobs, max_workers=10)

    # Startup.jobs — merge into career results
    startup_jobs = fetch_startup_jobs(search_terms, location, max_total=8)
    seen_c = {(j.get("url") or "").strip().lower() for j in career_jobs}
    for item in startup_jobs:
        key = (item.get("url") or "").strip().lower()
        if key not in seen_c:
            seen_c.add(key); career_jobs.append(item)

    # AICTE internships
    aicte_jobs = fetch_aicte_internships(search_terms=search_terms, max_total=12)

    return _ok({
        "search_terms":   search_terms,
        "adzuna_jobs":    adzuna_jobs,
        "career_jobs":    career_jobs,
        "aicte_jobs":     aicte_jobs,
        "portal_matches": portal_matches,
        "adzuna_error":   adzuna_error,
    })


# ── Portals ───────────────────────────────────────────────────────────────────
@app.route("/api/portals/relevant", methods=["POST"])
def portals_relevant():
    body    = _body()
    matched = get_relevant_portals(body.get("domains",[]), body.get("skills",[]),
                                   PORTALS, int(body.get("limit", 8)))
    return _ok({"portals": matched})


# ── Email ─────────────────────────────────────────────────────────────────────
@app.route("/api/email/preview", methods=["POST"])
def email_preview():
    body = _body()
    html = build_email_html(body.get("jobs",[]), body.get("portals",[]),
                            body.get("skills",[]), body.get("exp_level","Fresher"))
    return _ok({"html": html})


@app.route("/api/email/send", methods=["POST"])
def email_send():
    body      = _body()
    sender    = body.get("sender","")
    password  = body.get("password","")
    recipient = body.get("recipient","")
    if not all([sender, password, recipient]):
        return _err("'sender', 'password', and 'recipient' are required.")
    try:
        html    = build_email_html(body.get("jobs",[]), body.get("portals",[]),
                                   body.get("skills",[]), body.get("exp_level","Fresher"))
        subject = body.get("subject", "🚀 AI Job Alert")
        send_email(sender, password, recipient, subject, html)
        return _ok({"message": f"Email sent to {recipient}"})
    except Exception as exc:
        return _err(str(exc), 500)


# ── ATS Resume PDF ────────────────────────────────────────────────────────────
@app.route("/api/resume/build-pdf", methods=["POST"])
def resume_build_pdf():
    body            = _body()
    resume_text     = body.get("resume_text","")
    job_description = body.get("job_description","")
    candidate_name  = body.get("candidate_name","Candidate")

    if not resume_text or not job_description:
        return _err("'resume_text' and 'job_description' are required.")
    try:
        raw         = generate_ats_resume_json(resume_text, job_description, candidate_name)
        resume_dict = safe_parse_json(raw)
        if not resume_dict:
            return jsonify({"ok":False,"error":"AI returned unexpected format.","raw_json":raw}), 422
        pdf_bytes = build_resume_pdf(resume_dict)
        safe_name = re.sub(r"[^a-zA-Z0-9_\-]","_", candidate_name)
        return send_file(BytesIO(pdf_bytes), mimetype="application/pdf",
                         as_attachment=True, download_name=f"ATS_Resume_{safe_name}.pdf")
    except Exception as exc:
        return _err(str(exc), 500)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG","0") == "1"
    print(f"[JobRadar] Starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
