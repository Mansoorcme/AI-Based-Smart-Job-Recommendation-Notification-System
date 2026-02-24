"""
ats_resume.py — Gemini ATS resume rewriter + ReportLab PDF generator.
"""

import json
import re
from io import BytesIO

from reportlab.lib             import colors
from reportlab.lib.enums       import TA_CENTER
from reportlab.lib.pagesizes   import A4
from reportlab.lib.styles      import ParagraphStyle
from reportlab.lib.units       import inch
from reportlab.platypus        import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from gemini_client import gemini_generate    # direct import


def generate_ats_resume_json(resume_text: str, job_description: str, candidate_name: str) -> str:
    """Call Gemini to rewrite a resume for a specific JD. Returns raw JSON string."""
    prompt = f"""
You are an ATS resume expert.
RESUME: {resume_text[:3000]}
JOB DESCRIPTION: {job_description[:2000]}
NAME: {candidate_name}

Generate a fully ATS-optimised resume as JSON ONLY (no markdown, no code fences):
{{
  "name":"","title":"","email":"","phone":"","location":"","linkedin":"",
  "summary":"","skills":[],
  "experience":[{{"company":"","role":"","duration":"","bullets":[]}}],
  "education":[{{"degree":"","institution":"","year":"","gpa":""}}],
  "projects":[{{"name":"","description":"","impact":""}}],
  "certifications":[]
}}
"""
    return gemini_generate(prompt)


def safe_parse_json(text: str):
    """Strip markdown fences and parse JSON. Returns dict or None."""
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
        return json.loads(cleaned)
    except Exception:
        return None


def build_resume_pdf(d: dict) -> bytes:
    """Render resume dict to PDF bytes using ReportLab."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=.6*inch, rightMargin=.6*inch,
          topMargin=.6*inch,  bottomMargin=.6*inch)

    accent = colors.HexColor("#5b4cf5")
    dark   = colors.HexColor("#0d0f1c")
    gray   = colors.HexColor("#555555")
    lgray  = colors.HexColor("#dddddd")

    sN  = ParagraphStyle("N",  fontName="Helvetica-Bold",    fontSize=20, textColor=dark,   spaceAfter=2,  alignment=TA_CENTER)
    sT  = ParagraphStyle("T",  fontName="Helvetica",         fontSize=11, textColor=accent, spaceAfter=4,  alignment=TA_CENTER)
    sC  = ParagraphStyle("C",  fontName="Helvetica",         fontSize=8,  textColor=gray,   spaceAfter=8,  alignment=TA_CENTER)
    sSH = ParagraphStyle("SH", fontName="Helvetica-Bold",    fontSize=10, textColor=accent, spaceBefore=10,spaceAfter=3)
    sBD = ParagraphStyle("BD", fontName="Helvetica",         fontSize=9,  textColor=colors.HexColor("#222"), spaceAfter=2, leading=13)
    sBU = ParagraphStyle("BU", fontName="Helvetica",         fontSize=9,  textColor=colors.HexColor("#333"), spaceAfter=1, leading=12, leftIndent=12)
    sBL = ParagraphStyle("BL", fontName="Helvetica-Bold",    fontSize=9,  textColor=dark,   spaceAfter=1)
    sIT = ParagraphStyle("IT", fontName="Helvetica-Oblique", fontSize=8.5,textColor=gray,   spaceAfter=2)

    story = []
    hr    = lambda: HRFlowable(width="100%", thickness=0.5, color=lgray,  spaceAfter=4)
    ahr   = lambda: HRFlowable(width="100%", thickness=1,   color=accent, spaceAfter=6)
    sec   = lambda t: [story.append(Paragraph(t, sSH)), story.append(hr())]

    story += [Paragraph(d.get("name",""), sN), Paragraph(d.get("title",""), sT)]
    story.append(Paragraph("  |  ".join(x for x in [d.get("email"),d.get("phone"),
                            d.get("location"),d.get("linkedin")] if x), sC))
    story.append(ahr())

    if d.get("summary"):
        [story.append(Paragraph("PROFESSIONAL SUMMARY", sSH)), story.append(hr())]
        story.append(Paragraph(d["summary"], sBD))

    if d.get("skills"):
        [story.append(Paragraph("TECHNICAL SKILLS", sSH)), story.append(hr())]
        story.append(Paragraph("  •  ".join(d["skills"]), sBD))

    if d.get("experience"):
        [story.append(Paragraph("EXPERIENCE", sSH)), story.append(hr())]
        for e in d["experience"]:
            story += [Paragraph(f"{e.get('role','')} — {e.get('company','')}", sBL),
                      Paragraph(e.get("duration",""), sIT)]
            for b in e.get("bullets",[]): story.append(Paragraph(f"• {b}", sBU))
            story.append(Spacer(1,4))

    if d.get("education"):
        [story.append(Paragraph("EDUCATION", sSH)), story.append(hr())]
        for e in d["education"]:
            gpa = f" | GPA: {e['gpa']}" if e.get("gpa") else ""
            story.append(Paragraph(f"{e.get('degree','')} — {e.get('institution','')}{gpa} ({e.get('year','')})", sBD))

    if d.get("projects"):
        [story.append(Paragraph("PROJECTS", sSH)), story.append(hr())]
        for p in d["projects"]:
            story += [Paragraph(p.get("name",""), sBL), Paragraph(p.get("description",""), sBU)]
            if p.get("impact"): story.append(Paragraph(f"📈 {p['impact']}", sBU))
            story.append(Spacer(1,3))

    if d.get("certifications"):
        [story.append(Paragraph("CERTIFICATIONS", sSH)), story.append(hr())]
        for c in d["certifications"]: story.append(Paragraph(f"• {c}", sBU))

    doc.build(story)
    return buf.getvalue()
