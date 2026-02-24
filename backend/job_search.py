"""
job_search.py — Adzuna API, career pages (JobRadar), AICTE internships, startup.jobs.
"""

import re
import concurrent.futures
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import ADZUNA_APP_ID, ADZUNA_API_KEY, STARTUP_JOBS_URL, SCRAPE_HEADERS, ROLE_KEYWORDS  # direct import

try:
    from job_alerts import JobRadar as _JobRadar
    _HAS_JOB_RADAR = True
except ImportError:
    _HAS_JOB_RADAR = False


def _is_job_title(text: str) -> bool:
    t = text.lower().strip()
    return bool(text) and 4 <= len(t) <= 120 and any(kw in t for kw in ROLE_KEYWORDS)


def _resolve_href(href: str, base_url: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{href}"
    return base_url.rstrip("/") + "/" + href.lstrip("./")


# ── Adzuna ────────────────────────────────────────────────────────────────────

def fetch_adzuna_jobs(role: str, country: str = "in", exp_level: str = "Fresher",
                      location: str = "", n: int = 6) -> tuple:
    """Returns (list_of_jobs, error_string_or_None)."""
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return [], "Missing ADZUNA_APP_ID / ADZUNA_API_KEY in .env"

    params = {
        "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY,
        "what": role.strip(), "results_per_page": max(10, n),
        "sort_by": "date", "content-type": "application/json",
    }
    if location.strip():
        params["where"] = location.strip()

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 401: return [], "Adzuna auth failed (401)."
        if r.status_code == 403: return [], "Adzuna access denied (403)."
        if r.status_code == 429: return [], "Adzuna rate limit (429). Retry later."
        if r.status_code != 200: return [], f"Adzuna error {r.status_code}: {r.text[:200]}"

        results = r.json().get("results", [])
        if exp_level == "Fresher":
            pos = ["intern","internship","trainee","entry","junior","graduate","fresher","0-1"]
            neg = ["senior","lead","principal","manager","architect","2+ years","3+ years","5+ years"]
            filtered = [j for j in results
                        if any(p in f"{j.get('title','')} {j.get('description','')}".lower() for p in pos)
                        and not any(x in f"{j.get('title','')} {j.get('description','')}".lower() for x in neg)]
            results = filtered or results

        return [{
            "source":      "Adzuna",
            "title":       j.get("title","N/A"),
            "company":     j.get("company",{}).get("display_name","N/A"),
            "location":    j.get("location",{}).get("display_name","N/A"),
            "description": (j.get("description") or "")[:300],
            "url":         j.get("redirect_url","#"),
            "salary":      j.get("salary_min"),
        } for j in results[:n]], None

    except requests.exceptions.ConnectionError as e:
        return [], f"Network error: {e}"
    except requests.exceptions.Timeout:
        return [], "Adzuna API timed out."
    except Exception as e:
        return [], f"Unexpected error: {e}"


# ── Career Pages via JobRadar ─────────────────────────────────────────────────

def fetch_career_page_jobs(queries, location: str = "", max_total: int = 40) -> list:
    if not _HAS_JOB_RADAR:
        return []
    query_list = ([queries.strip()] if isinstance(queries, str)
                  else [str(q).strip() for q in (queries or []) if str(q).strip()])
    if not query_list:
        return []
    try:
        jr = _JobRadar(verbose=False, max_per_company=2, delay=0.05)
        results, seen = [], set()
        for idx, q in enumerate(query_list[:2]):
            for j in jr.search_jobs(q, companies=None, max_total=max_total):
                url     = getattr(j, "apply_url", "#")
                title   = getattr(j, "title", "N/A")
                company = getattr(j, "company", "N/A")
                key     = f"{title}|{company}|{url}".strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append({
                    "source":      "Career Page",
                    "title":       title,
                    "company":     company,
                    "location":    getattr(j, "location", location or "N/A"),
                    "description": (getattr(j, "description","") or "")[:300],
                    "url":         url,
                })
                if len(results) >= max_total:
                    return results[:max_total]
            if idx == 0 and len(results) >= min(16, max_total):
                break
        return results[:max_total]
    except Exception:
        return []


# ── AICTE Internships ─────────────────────────────────────────────────────────

def fetch_aicte_internships(search_terms: list = None, max_total: int = 12, max_pages: int = 3) -> list:
    base     = "https://internship.aicte-india.org"
    list_url = f"{base}/recentlyposted.php"
    api_url  = f"{base}/class/class_internship.php"
    terms    = [str(t).strip().lower() for t in (search_terms or []) if str(t).strip()]
    tokens   = [tok for t in terms for tok in re.split(r"[^a-z0-9]+", t) if len(tok) >= 3]

    session = requests.Session()
    headers = {**SCRAPE_HEADERS, "Referer": list_url}
    try:
        session.get(list_url, headers=headers, timeout=15)
    except Exception:
        return []

    out, fallback, seen = [], [], set()
    for page in range(1, max_pages + 1):
        try:
            r = session.post(api_url, data={"action":"load_internship","location":"all",
                "internship_type":"all","internship_stipend":"all","page":page},
                headers=headers, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
        except Exception:
            continue

        html = data.get("list","") or ""
        if "No Internship Found" in html:
            break

        soup  = BeautifulSoup(html, "html.parser")
        cards = soup.select(".internships-list")
        if not cards:
            continue

        for card in cards:
            def _t(sel):
                el = card.select_one(sel)
                return el.get_text(" ",strip=True) if el else ""

            title    = _t(".job-title") or "Internship Opportunity"
            company  = _t(".company-name") or "AICTE Portal"
            location = _t("li.location span") or "India"
            duration = _t("li.duration span")
            stipend  = ""
            for li in card.select("ul.job-supplement-attributes li"):
                k = (_t("h6")).lower()
                v = _t("span")
                if "stipend" in k:
                    stipend = v

            link_el = card.select_one("a[href]")
            href    = (link_el.get("href","").strip() if link_el else "") or list_url
            if href.startswith("/"):
                href = f"{base}{href}"
            elif href and not href.startswith("http"):
                href = f"{base}/{href.lstrip('./')}"

            desc = " | ".join(x for x in [
                f"Duration: {duration}" if duration else "",
                f"Stipend: {stipend}" if stipend else "",
            ] if x)

            hay     = f"{title} {company} {desc} {location}".lower()
            matched = (not terms) or any(t in hay for t in terms) or any(tok in hay for tok in tokens)
            key     = f"{title}|{company}|{href}".lower()
            if key in seen:
                continue
            seen.add(key)
            row = {"source":"AICTE Internship","title":title,"company":company,
                   "location":location,"description":desc[:300],"url":href}
            fallback.append(row)
            if matched:
                out.append(row)
                if len(out) >= max_total:
                    return out[:max_total]

    return (out or fallback)[:max_total]


# ── Startup.jobs ──────────────────────────────────────────────────────────────

def fetch_startup_jobs(search_terms: list, location: str = "", max_total: int = 8) -> list:
    url = STARTUP_JOBS_URL or "https://startup.jobs/"
    fallback = [{"source":"Startup Jobs","title":"Startup Jobs - Open Listings",
                 "company":"startup.jobs","location":location or "Global",
                 "description":"Direct link to startup.jobs listings.","url":url,"salary":None}]
    try:
        r    = requests.get(url, headers=SCRAPE_HEADERS, timeout=12, allow_redirects=True)
        body = r.text or ""
        if r.status_code in (401,403,429) or "just a moment" in body.lower():
            return fallback

        soup  = BeautifulSoup(body, "html.parser")
        terms = [t.lower() for t in (search_terms or []) if t]
        jobs, seen = [], set()
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            text = (a.get_text(" ",strip=True) or "").strip()
            if not href or ("/jobs/" not in href and "startup.jobs/" not in href):
                continue
            href = _resolve_href(href, "https://startup.jobs/")
            if not href.startswith("http"):
                continue
            text = text or "Startup Job Opening"
            if terms and not any(t in text.lower() for t in terms) and not _is_job_title(text):
                continue
            key = f"{text}|{href}".lower()
            if key in seen:
                continue
            seen.add(key)
            jobs.append({"source":"Startup Jobs","title":text[:120],"company":"startup.jobs",
                         "location":location or "Global","description":"From startup.jobs",
                         "url":href,"salary":None})
            if len(jobs) >= max_total:
                break
        return jobs or fallback
    except Exception:
        return fallback


# ── Link verifier ─────────────────────────────────────────────────────────────

def _is_link_valid(url: str, timeout: int = 8) -> bool:
    link = (url or "").strip()
    if not link or link == "#":
        return False
    try:
        h = requests.head(link, allow_redirects=True, timeout=timeout, headers=SCRAPE_HEADERS)
        if h.status_code == 404:
            return False
        if 200 <= h.status_code < 400:
            return True
        g = requests.get(link, allow_redirects=True, timeout=timeout, headers=SCRAPE_HEADERS, stream=True)
        g.close()
        return g.status_code != 404
    except requests.RequestException:
        return False


def filter_verified_career_jobs(jobs: list, max_workers: int = 10) -> list:
    if not jobs:
        return []
    verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        fm = {ex.submit(_is_link_valid, j.get("url","")): j for j in jobs}
        for future in concurrent.futures.as_completed(fm):
            try:
                if future.result():
                    verified.append(fm[future])
            except Exception:
                pass
    return verified
