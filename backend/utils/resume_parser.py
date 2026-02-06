import io
from PyPDF2 import PdfReader
from docx import Document

def parse_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return ""

def parse_docx(file_bytes: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return ""

def parse_resume(file_bytes: bytes, file_name: str) -> str:
    if file_name.lower().endswith('.pdf'):
        return parse_pdf(file_bytes)
    elif file_name.lower().endswith('.docx') or file_name.lower().endswith('.doc'):
        return parse_docx(file_bytes)
    else:
        return ""