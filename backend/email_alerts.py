"""
email_alerts.py — Email builder, SMTP sender, daily scheduler.
"""

import ssl
import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import SMTP_SERVER, SMTP_PORT    # direct import


def build_email_html(jobs: list, portals: list, skills: list, exp_level: str) -> str:
    jobs_html = ""
    for j in jobs[:10]:
        tag_col = "#5b4cf5" if j.get("source") == "Adzuna" else "#16a34a"
        tag_lbl = j.get("source","Adzuna")
        sal_str = f"₹{int(j['salary']):,}" if j.get("salary") else ""
        jobs_html += f"""
<div style="background:#f8f8ff;border-left:4px solid {tag_col};border-radius:8px;
            padding:16px 18px;margin:10px 0;">
  <span style="background:{tag_col};color:white;font-size:10px;padding:2px 9px;
               border-radius:10px;font-weight:700;">{tag_lbl}</span>
  <h3 style="margin:7px 0 4px;color:#0d0f1c;font-size:15px;font-weight:700;">{j.get('title','N/A')}</h3>
  <p style="margin:2px 0;color:#555;font-size:13px;">
    🏢 {j.get('company','N/A')} &nbsp;|&nbsp; 📍 {j.get('location','N/A')}
    {(' &nbsp;|&nbsp; 💰 ' + sal_str) if sal_str else ''}
  </p>
  <p style="margin:6px 0 0;font-size:12px;color:#888;">{(j.get('description') or '')[:200]}</p>
  <a href="{j.get('url','#')}"
     style="display:inline-block;margin-top:10px;background:{tag_col};color:white;
            text-decoration:none;padding:6px 16px;border-radius:6px;font-size:12px;font-weight:700;">
    Apply Now →
  </a>
</div>"""

    portal_chips = "".join(
        f'<a href="{p["link"]}" style="display:inline-block;background:#ede9fe;color:#5b4cf5;'
        f'padding:6px 13px;border-radius:20px;margin:4px;font-size:12px;text-decoration:none;font-weight:600;">'
        f'🏢 {p["title"]}</a>'
        for p in portals[:10]
    )
    portals_section = (
        f'<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">'
        f'<h2 style="font-size:15px;color:#0d0f1c;">🏢 Company Career Portals</h2>'
        f'{portal_chips}'
        if portal_chips else ""
    )

    return f"""
<html><body style="font-family:'Segoe UI',sans-serif;max-width:640px;margin:0 auto;color:#333;">
  <div style="background:linear-gradient(135deg,#5b4cf5,#7b6ff8);padding:30px;
              border-radius:14px 14px 0 0;text-align:center;">
    <h1 style="color:white;margin:0;font-size:22px;font-weight:800;">🚀 Your Job Alert</h1>
    <p style="color:rgba(255,255,255,.85);margin:8px 0 0;font-size:14px;">
      {len(jobs)} openings found &nbsp;|&nbsp; Level: <strong>{exp_level}</strong>
    </p>
  </div>
  <div style="background:white;padding:26px;border-radius:0 0 14px 14px;border:1px solid #eee;">
    <p style="color:#666;font-size:13px;margin-bottom:16px;">
      Skills matched: <strong>{', '.join(skills[:8])}</strong>
    </p>
    <h2 style="font-size:15px;color:#0d0f1c;margin-bottom:10px;">📋 Live Job Openings</h2>
    {jobs_html}
    {portals_section}
    <p style="color:#bbb;font-size:11px;text-align:center;margin-top:24px;">
      JobRadar AI · {datetime.now().strftime('%B %d, %Y %H:%M')}
    </p>
  </div>
</body></html>"""


def send_email(sender: str, password: str, recipient: str, subject: str, html: str) -> None:
    """Send HTML email via SMTP. Supports port 587 (STARTTLS) and 465 (SSL)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html"))

    if SMTP_PORT == 465:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as s:
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())


def schedule_daily_email(sender: str, password: str, recipient: str,
                         html_fn, hour: int, minute: int) -> None:
    """Start a daemon thread that sends a job alert email once per day at hour:minute."""
    def _worker():
        while True:
            now    = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            time.sleep((target - now).total_seconds())
            try:
                send_email(sender, password, recipient,
                           f"🚀 Daily Job Alert — {datetime.now().strftime('%b %d, %Y')}",
                           html_fn())
            except Exception as exc:
                print(f"[Scheduler] Failed: {exc}")

    threading.Thread(target=_worker, daemon=True).start()
