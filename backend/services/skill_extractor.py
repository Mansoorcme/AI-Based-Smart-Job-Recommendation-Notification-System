import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_skills(resume_text):
    doc = nlp(resume_text.lower())

    skill_keywords = set()
    predefined_skills = [
        "python", "java", "sql", "machine learning",
        "deep learning", "nlp", "data analysis",
        "backend", "api", "cloud", "cyber security"
    ]

    for token in doc:
        if token.text in predefined_skills:
            skill_keywords.add(token.text)

    return list(skill_keywords)