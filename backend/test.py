import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
smtp_host = os.getenv("SMTP_HOST")
smtp_port = os.getenv("SMTP_PORT")
smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")
admin_email = os.getenv("ADMIN_EMAIL")
print(f"SMTP Host: {smtp_host}")
print(f"SMTP Port: {smtp_port}")
print(f"SMTP User: {smtp_user}") 
print(f"SMTP Pass: {smtp_pass}")
print(f"Admin Email: {admin_email}")