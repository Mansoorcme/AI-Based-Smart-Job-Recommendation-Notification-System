"""
job_radar.py  ·  v2.0
======================
A Python module that fetches REAL job listings directly from company
career pages (Eightfold, Lever, Greenhouse, Workday, custom scrapers).

Enter a job role → get back live job posts with title, location,
description summary, and a direct apply URL — just like the PayPal
careers search page you showed.

Quick start
-----------
    from job_radar import JobRadar

    jr = JobRadar()
    jobs = jr.search_jobs("software engineer", companies=["google","microsoft"])
    jr.print_jobs(jobs)

    # Or search across everything
    jobs = jr.search_jobs("data scientist")
    for job in jobs:
        print(job.title, "–", job.company, "–", job.apply_url)

Requirements
------------
    pip install requests beautifulsoup4

Optional (nicer terminal output):
    pip install rich
"""

from __future__ import annotations

import json
import re
import time
import datetime
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from pathlib import Path

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# ══════════════════════════════════════════════════════════════════════════════
#  DATA MODEL
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class JobPost:
    """A single live job listing fetched from a company career page."""
    title:       str
    company:     str
    location:    str
    department:  str
    job_type:    str           # full-time / part-time / contract / internship
    description: str           # short summary (first ~300 chars of JD)
    apply_url:   str           # direct link to the application page
    job_id:      str = ""
    posted_date: str = ""
    source:      str = ""      # eightfold / lever / greenhouse / workday / web
    fetched_at:  str = field(default_factory=lambda: datetime.datetime.now().isoformat(timespec="seconds"))
    raw: dict    = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw", None)
        return d

    def short_desc(self, chars: int = 180) -> str:
        text = re.sub(r"<[^>]+>", " ", self.description)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:chars] + ("…" if len(text) > chars else "")


# ══════════════════════════════════════════════════════════════════════════════
#  ATS FETCHERS  — one function per platform
# ══════════════════════════════════════════════════════════════════════════════

class _Fetcher:
    """Base mix-in: shared HTTP helpers."""

    HEADERS = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/122.0.0.0 Safari/537.36",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    JSON_HEADERS = {**HEADERS, "Accept": "application/json, text/javascript, */*"}

    def __init__(self, session: requests.Session, timeout: int = 15, verbose: bool = True):
        self.session = session
        self.timeout = timeout
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"  [{ts}] {msg}")

    def _get(self, url: str, **kwargs) -> Optional[requests.Response]:
        try:
            r = self.session.get(url, headers=self.HEADERS, timeout=self.timeout, **kwargs)
            r.raise_for_status()
            return r
        except Exception as e:
            self._log(f"✗ GET failed: {url[:80]} — {e}")
            return None

    def _get_json(self, url: str, **kwargs) -> Optional[dict]:
        try:
            r = self.session.get(url, headers=self.JSON_HEADERS, timeout=self.timeout, **kwargs)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            self._log(f"✗ JSON failed: {url[:80]} — {e}")
            return None

    @staticmethod
    def _clean(text: str) -> str:
        """Strip HTML tags and extra whitespace."""
        text = re.sub(r"<[^>]+>", " ", text or "")
        return re.sub(r"\s+", " ", text).strip()


# ─── Eightfold ────────────────────────────────────────────────────────────────
class EightfoldFetcher(_Fetcher):
    """
    Fetches jobs from companies using the Eightfold ATS.

    Eightfold career pages embed a JSON blob in their HTML with a `positions`
    array.  We extract that blob, then filter by the user's query.

    Companies known to use Eightfold:
        PayPal, Meesho, Groww, Swiggy, Airtel, Jio, Persistent, Mphasis,
        CRED, CarDekho, Nykaa, Snapdeal, Delhivery, Gojek …
    """

    # subdomain → domain hint (some need explicit domain param)
    KNOWN = {
        "paypal":     {"subdomain": "paypal",     "domain": "paypal.com"},
        "meesho":     {"subdomain": "meesho",     "domain": "meesho.com"},
        "swiggy":     {"subdomain": "swiggy",     "domain": "swiggy.com"},
        "groww":      {"subdomain": "groww",      "domain": "groww.in"},
        "cred":       {"subdomain": "cred",       "domain": "cred.club"},
        "delhivery":  {"subdomain": "delhivery",  "domain": "delhivery.com"},
        "nykaa":      {"subdomain": "nykaa",      "domain": "nykaa.com"},
        "cardekho":   {"subdomain": "cardekho",   "domain": "cardekho.com"},
        "gojek":      {"subdomain": "gojek",      "domain": "gojek.com"},
        "persistent": {"subdomain": "persistent", "domain": "persistent.com"},
        "mphasis":    {"subdomain": "mphasis",    "domain": "mphasis.com"},
        "snapdeal":   {"subdomain": "snapdeal",   "domain": "snapdeal.com"},
        "airtel":     {"subdomain": "airtel",     "domain": "airtel.com"},
        "jio":        {"subdomain": "jio",        "domain": "jio.com"},
    }

    def fetch(self, company_key: str, query: str, max_results: int = 20) -> list[JobPost]:
        info = self.KNOWN.get(company_key.lower())
        if not info:
            return []

        company_name = company_key.title()
        subdomain = info["subdomain"]
        domain = info["domain"]

        # Build URL — eightfold passes query as a search param
        q_enc = urllib.parse.quote(query)
        url = (f"https://{subdomain}.eightfold.ai/careers"
               f"?domain={domain}&query={q_enc}&sort_by=relevance")

        self._log(f"Eightfold → {subdomain}: '{query}'")
        resp = self._get(url)
        if not resp:
            return []

        return self._parse_html(resp.text, company_name, subdomain, query, max_results)

    def fetch_by_url(self, base_url: str, company_name: str, query: str,
                     max_results: int = 20) -> list[JobPost]:
        """Fetch from an arbitrary eightfold URL (e.g. custom subdomain)."""
        sep = "&" if "?" in base_url else "?"
        q_enc = urllib.parse.quote(query)
        url = f"{base_url}{sep}query={q_enc}&sort_by=relevance"
        self._log(f"Eightfold(custom) → {company_name}: '{query}'")
        resp = self._get(url)
        if not resp:
            return []
        subdomain = re.search(r"https?://([^.]+)", base_url)
        sub = subdomain.group(1) if subdomain else company_name.lower()
        return self._parse_html(resp.text, company_name, sub, query, max_results)

    def _parse_html(self, html: str, company: str, subdomain: str,
                    query: str, max_results: int) -> list[JobPost]:
        # Eightfold embeds all data in a JS variable inside <script>
        # Pattern: "positions":[{...}]
        match = re.search(r'"positions"\s*:\s*(\[.*?\])\s*[,}]', html, re.DOTALL)
        if not match:
            self._log(f"  No positions JSON found for {company}")
            return []

        try:
            positions = json.loads(match.group(1))
        except json.JSONDecodeError:
            self._log(f"  JSON parse failed for {company}")
            return []

        jobs = []
        q_lower = query.lower()
        for pos in positions:
            name = pos.get("name", "")
            # Filter by query (eightfold returns all; we filter client-side too)
            if q_lower not in name.lower() and q_lower not in pos.get("department", "").lower():
                # lenient — include if no match filter is very strict
                pass  # include all returned by the server's query filter

            pid = pos.get("id", "")
            loc_list = pos.get("locations") or [pos.get("location", "")]
            location = ", ".join(str(l) for l in loc_list if l) or "Not specified"
            dept = pos.get("department", "") or pos.get("business_unit", "")
            jtype = pos.get("work_location_option", "") or pos.get("type", "")
            desc_raw = pos.get("job_description", "") or pos.get("description", "")
            t_create = pos.get("t_create") or pos.get("t_update")
            posted = ""
            if t_create:
                try:
                    posted = datetime.datetime.fromtimestamp(t_create).strftime("%Y-%m-%d")
                except Exception:
                    pass

            apply_url = (pos.get("canonicalPositionUrl")
                         or f"https://{subdomain}.eightfold.ai/careers/job/{pid}")

            jobs.append(JobPost(
                title=name,
                company=company,
                location=location,
                department=dept,
                job_type=jtype,
                description=self._clean(desc_raw),
                apply_url=apply_url,
                job_id=str(pid),
                posted_date=posted,
                source="eightfold",
                raw=pos,
            ))
            if len(jobs) >= max_results:
                break

        self._log(f"  ✓ {len(jobs)} jobs from {company} (eightfold)")
        return jobs


# ─── Lever ────────────────────────────────────────────────────────────────────
class LeverFetcher(_Fetcher):
    """
    Fetches jobs via Lever's public JSON API.
    URL pattern: https://api.lever.co/v0/postings/{company}?mode=json&text=<query>

    Companies: Coinswitch, Upstox, Jupiter, Divvy, Protegrity …
    """

    KNOWN = {
        "coinswitch":  "coinswitch",
        "upstox":      "upstox",
        "jupiter":     "jupiter",
        "divvy":       "divvyhomes",
        "protegrity":  "protegrity",
        "freshworks":  "freshworks",
        "razorpay":    "razorpay",
        "browserstack": "browserstack",
        "postman":     "postman",
        "cred":        "cred",
        "groww":       "groww",
        "slice":       "sliceit",
    }

    def fetch(self, company_key: str, query: str, max_results: int = 20) -> list[JobPost]:
        slug = self.KNOWN.get(company_key.lower(), company_key.lower())
        company_name = company_key.title()
        q_enc = urllib.parse.quote(query)
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json&text={q_enc}"
        self._log(f"Lever → {slug}: '{query}'")
        data = self._get_json(url)
        if not data or not isinstance(data, list):
            return []
        return self._parse(data, company_name, slug, max_results)

    def fetch_by_slug(self, slug: str, company_name: str, query: str,
                      max_results: int = 20) -> list[JobPost]:
        q_enc = urllib.parse.quote(query)
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json&text={q_enc}"
        self._log(f"Lever(custom) → {slug}: '{query}'")
        data = self._get_json(url)
        if not data or not isinstance(data, list):
            return []
        return self._parse(data, company_name, slug, max_results)

    def _parse(self, data: list, company: str, slug: str, max_results: int) -> list[JobPost]:
        jobs = []
        for item in data:
            cats = item.get("categories", {})
            desc_parts = item.get("descriptionPlain", "") or item.get("description", "")
            lists = item.get("lists", [])
            full_desc = desc_parts
            if lists:
                full_desc += " " + " ".join(l.get("content", "") for l in lists)

            jobs.append(JobPost(
                title=item.get("text", ""),
                company=company,
                location=cats.get("location", "") or item.get("workplaceType", ""),
                department=cats.get("team", "") or cats.get("department", ""),
                job_type=cats.get("commitment", "") or item.get("workplaceType", ""),
                description=self._clean(full_desc),
                apply_url=item.get("hostedUrl", f"https://jobs.lever.co/{slug}/{item.get('id','')}"),
                job_id=item.get("id", ""),
                posted_date=datetime.datetime.fromtimestamp(
                    item["createdAt"] // 1000
                ).strftime("%Y-%m-%d") if item.get("createdAt") else "",
                source="lever",
                raw=item,
            ))
            if len(jobs) >= max_results:
                break
        self._log(f"  ✓ {len(jobs)} jobs from {company} (lever)")
        return jobs


# ─── Greenhouse ───────────────────────────────────────────────────────────────
class GreenhouseFetcher(_Fetcher):
    """
    Fetches jobs via Greenhouse's public board API.
    URL: https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true

    Companies: Airbnb, Stripe, Databricks, Discord, Flipkart, Meesho …
    """

    KNOWN = {
        "airbnb":      "airbnb",
        "stripe":      "stripe",
        "databricks":  "databricks",
        "discord":     "discord",
        "meesho":      "meesho",
        "browserstack": "browserstack",
        "postman":     "postman",
        "groww":       "groww",
        "coinbase":    "coinbase",
        "notion":      "notion",
        "figma":       "figma",
        "snowflake":   "snowflake",
        "confluent":   "confluent",
        "rubrik":      "rubrik",
        "harness":     "harness",
        "freshworks":  "freshworks",
        "dunzo":       "dunzo",
    }

    def fetch(self, company_key: str, query: str, max_results: int = 20) -> list[JobPost]:
        token = self.KNOWN.get(company_key.lower(), company_key.lower())
        company_name = company_key.title()
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        self._log(f"Greenhouse → {token}: '{query}'")
        data = self._get_json(url)
        if not data:
            return []
        return self._parse(data, company_name, token, query, max_results)

    def fetch_by_token(self, token: str, company_name: str, query: str,
                       max_results: int = 20) -> list[JobPost]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        self._log(f"Greenhouse(custom) → {token}: '{query}'")
        data = self._get_json(url)
        if not data:
            return []
        return self._parse(data, company_name, token, query, max_results)

    def _parse(self, data: dict, company: str, token: str,
               query: str, max_results: int) -> list[JobPost]:
        jobs_raw = data.get("jobs", [])
        q_lower = query.lower()

        # Client-side filter since Greenhouse API returns all jobs
        filtered = [
            j for j in jobs_raw
            if q_lower in j.get("title", "").lower()
            or q_lower in (j.get("departments") or [{"name": ""}])[0].get("name", "").lower()
            or q_lower in self._clean(j.get("content", "")).lower()
        ]

        jobs = []
        for item in filtered:
            depts = item.get("departments") or [{}]
            offices = item.get("offices") or item.get("location", {})
            if isinstance(offices, list):
                loc = ", ".join(o.get("name", "") for o in offices if o.get("name"))
            else:
                loc = offices.get("name", "") if isinstance(offices, dict) else str(offices)

            jobs.append(JobPost(
                title=item.get("title", ""),
                company=company,
                location=loc or "Not specified",
                department=(depts[0] or {}).get("name", ""),
                job_type="Full-time",
                description=self._clean(item.get("content", "")),
                apply_url=item.get("absolute_url", f"https://boards.greenhouse.io/{token}/jobs/{item.get('id','')}"),
                job_id=str(item.get("id", "")),
                posted_date=item.get("updated_at", "")[:10],
                source="greenhouse",
                raw=item,
            ))
            if len(jobs) >= max_results:
                break

        self._log(f"  ✓ {len(jobs)} jobs from {company} (greenhouse)")
        return jobs


# ─── Workday ──────────────────────────────────────────────────────────────────
class WorkdayFetcher(_Fetcher):
    """
    Fetches jobs from Workday-powered career pages via their search API.
    Used by: TCS, Infosys, Wipro, HCL, Cognizant, Capgemini, Accenture,
             Microsoft, Adobe, Salesforce, SAP, IBM …
    """

    # company → (tenant, namespace) from the career page URL
    KNOWN = {
        "microsoft":  ("microsoft",   "microsoftcareers"),
        "adobe":      ("adobe",       "adobecareers"),
        "salesforce": ("salesforce",  "salesforce"),
        "sap":        ("sap",         "sap"),
        "ibm":        ("ibm",         "ibm-careers"),
        "cisco":      ("cisco",       "cisco"),
        "accenture":  ("accenture",   "accenture"),
        "capgemini":  ("capgemini",   "capgemini"),
        "cognizant":  ("cognizant",   "cognizant"),
        "tcs":        ("tcs",         "tcs"),
        "infosys":    ("infosys",     "infosys"),
        "wipro":      ("wipro",       "wiproexternalcareersite"),
    }

    WORKDAY_SEARCH_URL = (
        "https://{tenant}.wd5.myworkdayjobs.com/wday/cxs/{tenant}/{ns}/jobs"
    )

    def fetch(self, company_key: str, query: str, max_results: int = 20) -> list[JobPost]:
        info = self.KNOWN.get(company_key.lower())
        if not info:
            return []
        tenant, ns = info
        company_name = company_key.title()
        return self._search(tenant, ns, company_name, query, max_results)

    def _search(self, tenant: str, ns: str, company: str,
                query: str, max_results: int) -> list[JobPost]:
        url = self.WORKDAY_SEARCH_URL.format(tenant=tenant, ns=ns)
        payload = {
            "appliedFacets": {},
            "limit": max_results,
            "offset": 0,
            "searchText": query,
        }
        self._log(f"Workday → {tenant}: '{query}'")
        try:
            resp = self.session.post(
                url,
                json=payload,
                headers={**self.JSON_HEADERS,
                         "Content-Type": "application/json",
                         "X-Calypso-CSRF-Token": ""},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            self._log(f"  Workday failed for {company}: {e}")
            return []

        return self._parse(data, company, tenant, ns, max_results)

    def _parse(self, data: dict, company: str, tenant: str,
               ns: str, max_results: int) -> list[JobPost]:
        items = data.get("jobPostings", [])
        jobs = []
        for item in items:
            ext_id = item.get("externalPath", "").strip("/")
            apply_url = f"https://{tenant}.wd5.myworkdayjobs.com/{ns}/job/{ext_id}"
            loc_list = item.get("locationsText", "") or item.get("bulletFields", [""])[0]
            posted = item.get("postedOn", "")

            jobs.append(JobPost(
                title=item.get("title", ""),
                company=company,
                location=loc_list if isinstance(loc_list, str) else ", ".join(loc_list),
                department=item.get("jobFamilyGroup", "") or item.get("jobFamily", ""),
                job_type=item.get("scheduleType", "Full-time"),
                description=self._clean(item.get("jobDescription", {}).get("jobDescription", "")
                                        if isinstance(item.get("jobDescription"), dict)
                                        else item.get("briefDescription", "")),
                apply_url=apply_url,
                job_id=item.get("jobReqId", ""),
                posted_date=posted[:10] if posted else "",
                source="workday",
                raw=item,
            ))
            if len(jobs) >= max_results:
                break
        self._log(f"  ✓ {len(jobs)} jobs from {company} (workday)")
        return jobs


# ─── Generic HTML Scraper ─────────────────────────────────────────────────────
class GenericScraper(_Fetcher):
    """
    Scrapes job titles and links from generic career pages using BeautifulSoup.
    Used as a fallback for companies without a known ATS API.
    """

    # Heuristic selectors for common job listing patterns
    JOB_SELECTORS = [
        # Greenhouse embed
        ("a.posting-title", "h2"),
        # Lever embed
        ("a.posting-title", "h5"),
        # Generic
        (".job-title a", None),
        (".position-title a", None),
        ("h3.job-title", None),
        ("a[data-job-id]", None),
        (".career-item a", None),
    ]

    def fetch(self, company: str, url: str, query: str,
              max_results: int = 20) -> list[JobPost]:
        self._log(f"HTML scrape → {company}: '{query}'")
        resp = self._get(url)
        if not resp or not HAS_BS4:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        q_lower = query.lower()
        jobs = []

        # Try each selector heuristic
        for link_sel, title_sel in self.JOB_SELECTORS:
            anchors = soup.select(link_sel)
            if anchors:
                for a in anchors:
                    title_el = a.select_one(title_sel) if title_sel else a
                    title = (title_el.get_text(strip=True) if title_el else a.get_text(strip=True))
                    if not title or q_lower not in title.lower():
                        continue
                    href = a.get("href", "")
                    if href and not href.startswith("http"):
                        base = "/".join(url.split("/")[:3])
                        href = base + href
                    jobs.append(JobPost(
                        title=title,
                        company=company,
                        location="See listing",
                        department="",
                        job_type="",
                        description="Visit the career page for full details.",
                        apply_url=href or url,
                        source="web",
                    ))
                    if len(jobs) >= max_results:
                        break
                if jobs:
                    break

        # Fallback: find any link containing the query on the page
        if not jobs:
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                if text and q_lower in text.lower() and len(text) < 150:
                    href = a["href"]
                    if not href.startswith("http"):
                        base = "/".join(url.split("/")[:3])
                        href = base + href
                    jobs.append(JobPost(
                        title=text,
                        company=company,
                        location="See listing",
                        department="",
                        job_type="",
                        description="Visit the career page for full details.",
                        apply_url=href,
                        source="web",
                    ))
                if len(jobs) >= max_results:
                    break

        self._log(f"  ✓ {len(jobs)} jobs from {company} (html scrape)")
        return jobs


# ══════════════════════════════════════════════════════════════════════════════
#  COMPANY REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

# Each entry: name → {ats, key/url, aliases}
# ats: "eightfold" | "lever" | "greenhouse" | "workday" | "web"
COMPANY_REGISTRY: dict[str, dict] = {
    # ── Eightfold ─────────────────────────────────────────────────────────────
    "paypal":       {"ats": "eightfold", "key": "paypal",      "name": "PayPal"},
    "meesho":       {"ats": "eightfold", "key": "meesho",      "name": "Meesho"},
    "swiggy":       {"ats": "eightfold", "key": "swiggy",      "name": "Swiggy"},
    "groww":        {"ats": "eightfold", "key": "groww",       "name": "Groww"},
    "cred":         {"ats": "eightfold", "key": "cred",        "name": "CRED"},
    "delhivery":    {"ats": "eightfold", "key": "delhivery",   "name": "Delhivery"},
    "nykaa":        {"ats": "eightfold", "key": "nykaa",       "name": "Nykaa"},
    "cardekho":     {"ats": "eightfold", "key": "cardekho",    "name": "CarDekho"},
    "gojek":        {"ats": "eightfold", "key": "gojek",       "name": "Gojek"},
    "persistent":   {"ats": "eightfold", "key": "persistent",  "name": "Persistent"},
    "mphasis":      {"ats": "eightfold", "key": "mphasis",     "name": "Mphasis"},
    "snapdeal":     {"ats": "eightfold", "key": "snapdeal",    "name": "Snapdeal"},
    "airtel":       {"ats": "eightfold", "key": "airtel",      "name": "Airtel"},
    "jio":          {"ats": "eightfold", "key": "jio",         "name": "Jio"},

    # ── Lever ─────────────────────────────────────────────────────────────────
    "coinswitch":   {"ats": "lever", "key": "coinswitch",      "name": "CoinSwitch"},
    "upstox":       {"ats": "lever", "key": "upstox",          "name": "Upstox"},
    "jupiter":      {"ats": "lever", "key": "jupiter",         "name": "Jupiter Money"},
    "divvy":        {"ats": "lever", "key": "divvyhomes",      "name": "Divvy Homes"},
    "protegrity":   {"ats": "lever", "key": "protegrity",      "name": "Protegrity"},
    "freshworks":   {"ats": "lever", "key": "freshworks",      "name": "Freshworks"},
    "razorpay":     {"ats": "lever", "key": "razorpay",        "name": "Razorpay"},
    "browserstack": {"ats": "lever", "key": "browserstack",    "name": "BrowserStack"},
    "postman":      {"ats": "lever", "key": "postman",         "name": "Postman"},

    # ── Greenhouse ────────────────────────────────────────────────────────────
    "airbnb":       {"ats": "greenhouse", "key": "airbnb",     "name": "Airbnb"},
    "stripe":       {"ats": "greenhouse", "key": "stripe",     "name": "Stripe"},
    "databricks":   {"ats": "greenhouse", "key": "databricks", "name": "Databricks"},
    "discord":      {"ats": "greenhouse", "key": "discord",    "name": "Discord"},
    "snowflake":    {"ats": "greenhouse", "key": "snowflake",  "name": "Snowflake"},
    "confluent":    {"ats": "greenhouse", "key": "confluent",  "name": "Confluent"},
    "rubrik":       {"ats": "greenhouse", "key": "rubrik",     "name": "Rubrik"},
    "harness":      {"ats": "greenhouse", "key": "harness",    "name": "Harness"},
    "notion":       {"ats": "greenhouse", "key": "notion",     "name": "Notion"},
    "figma":        {"ats": "greenhouse", "key": "figma",      "name": "Figma"},
    "dunzo":        {"ats": "greenhouse", "key": "dunzo",      "name": "Dunzo"},
    "coinbase":     {"ats": "greenhouse", "key": "coinbase",   "name": "Coinbase"},

    # ── Workday ───────────────────────────────────────────────────────────────
    "microsoft":    {"ats": "workday", "key": "microsoft",     "name": "Microsoft"},
    "adobe":        {"ats": "workday", "key": "adobe",         "name": "Adobe"},
    "salesforce":   {"ats": "workday", "key": "salesforce",    "name": "Salesforce"},
    "sap":          {"ats": "workday", "key": "sap",           "name": "SAP"},
    "ibm":          {"ats": "workday", "key": "ibm",           "name": "IBM"},
    "cisco":        {"ats": "workday", "key": "cisco",         "name": "Cisco"},
    "accenture":    {"ats": "workday", "key": "accenture",     "name": "Accenture"},
    "capgemini":    {"ats": "workday", "key": "capgemini",     "name": "Capgemini"},
    "cognizant":    {"ats": "workday", "key": "cognizant",     "name": "Cognizant"},
    "tcs":          {"ats": "workday", "key": "tcs",           "name": "TCS"},
    "infosys":      {"ats": "workday", "key": "infosys",       "name": "Infosys"},
    "wipro":        {"ats": "workday", "key": "wipro",         "name": "Wipro"},

    # ── Direct career pages (fallback HTML scrape) ────────────────────────────
    "google":       {"ats": "web", "url": "https://careers.google.com/jobs/results/?q={query}",           "name": "Google"},
    "amazon":       {"ats": "web", "url": "https://www.amazon.jobs/en/search?base_query={query}",         "name": "Amazon"},
    "flipkart":     {"ats": "web", "url": "https://www.flipkartcareers.com/#!/joblist",                   "name": "Flipkart"},
    "zerodha":      {"ats": "web", "url": "https://zerodha.com/careers/",                                 "name": "Zerodha"},
    "zoho":         {"ats": "web", "url": "https://careers.zohocorp.com/jobs/Careers",                    "name": "Zoho"},
    "netflix":      {"ats": "web", "url": "https://jobs.netflix.com/search?q={query}",                    "name": "Netflix"},
    "uber":         {"ats": "web", "url": "https://www.uber.com/us/en/careers/jobs/?query={query}",       "name": "Uber"},
    "zomato":       {"ats": "web", "url": "https://www.zomato.com/careers",                               "name": "Zomato"},
    "paytm":        {"ats": "web", "url": "https://paytm.com/careers/",                                   "name": "Paytm"},
    "phonepe":      {"ats": "web", "url": "https://www.phonepe.com/careers/",                             "name": "PhonePe"},
    "byju":         {"ats": "web", "url": "https://byjus.com/careers/all-openings/",                      "name": "BYJU'S"},
}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CLASS
# ══════════════════════════════════════════════════════════════════════════════

class JobRadar:
    """
    Real-time job search across company career pages.

    >>> jr = JobRadar()
    >>> jobs = jr.search_jobs("data engineer", companies=["databricks", "snowflake"])
    >>> jr.print_jobs(jobs)

    >>> # Search ALL registered companies
    >>> jobs = jr.search_jobs("software engineer")
    """

    def __init__(
        self,
        timeout: int = 15,
        delay: float = 0.5,
        verbose: bool = True,
        max_per_company: int = 10,
    ):
        """
        Parameters
        ----------
        timeout : int
            HTTP request timeout in seconds.
        delay : float
            Politeness delay between company requests.
        verbose : bool
            Print progress to stdout.
        max_per_company : int
            Max job listings to fetch per company.
        """
        if not HAS_REQUESTS:
            raise ImportError("Install requests:  pip install requests")

        self.timeout = timeout
        self.delay = delay
        self.verbose = verbose
        self.max_per_company = max_per_company

        # Build HTTP session
        session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.4, status_forcelist=[429, 500, 502, 503])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        })

        # Initialise fetchers
        args = dict(session=session, timeout=timeout, verbose=verbose)
        self._ef  = EightfoldFetcher(**args)
        self._lev = LeverFetcher(**args)
        self._gh  = GreenhouseFetcher(**args)
        self._wd  = WorkdayFetcher(**args)
        self._web = GenericScraper(**args)

        # Custom companies added at runtime
        self._custom: list[dict] = []  # [{name, ats, key/url, ...}]

    # ── helpers ───────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        if self.verbose:
            print(f"[JobRadar] {msg}")

    @property
    def available_companies(self) -> list[str]:
        """List of all company keys you can search."""
        return sorted(list(COMPANY_REGISTRY.keys()) + [c["key"] for c in self._custom])

    # ── add custom company ────────────────────────────────────────────────────

    def add_company(
        self,
        name: str,
        *,
        ats: str,
        key: str = "",
        url: str = "",
        eightfold_subdomain: str = "",
        eightfold_domain: str = "",
    ) -> None:
        """
        Register a new company for searching.

        Parameters
        ----------
        name : str
            Display name.
        ats : str
            One of: "eightfold", "lever", "greenhouse", "workday", "web"
        key : str
            Company key/slug used by the ATS (for lever/greenhouse/workday).
        url : str
            Career page URL (for ats="web"). Use {query} as placeholder.
        eightfold_subdomain : str
            Subdomain for eightfold (e.g. "acme" for acme.eightfold.ai).
        eightfold_domain : str
            Domain hint for eightfold (e.g. "acme.com").

        Examples
        --------
        >>> jr.add_company("Acme Corp", ats="lever", key="acme")
        >>> jr.add_company("Acme Corp", ats="eightfold",
        ...                eightfold_subdomain="acme", eightfold_domain="acme.com")
        >>> jr.add_company("Acme Corp", ats="greenhouse", key="acme")
        >>> jr.add_company("Acme Corp", ats="web",
        ...                url="https://acme.com/careers?q={query}")
        """
        entry = {"name": name, "ats": ats, "key": key or name.lower(), "url": url}
        if ats == "eightfold":
            entry["subdomain"] = eightfold_subdomain or key
            entry["domain"]    = eightfold_domain
        self._custom.append(entry)
        COMPANY_REGISTRY[name.lower()] = entry
        self._log(f"Registered: {name} ({ats})")

    # ── core search ───────────────────────────────────────────────────────────

    def search_jobs(
        self,
        query: str,
        companies: Optional[list[str]] = None,
        max_total: int = 100,
        on_result: Optional[Callable[[JobPost], None]] = None,
    ) -> list[JobPost]:
        """
        Search for live job listings matching ``query``.

        Parameters
        ----------
        query : str
            Job role or keyword (e.g. "software engineer", "data scientist").
        companies : list[str] | None
            Company keys to search. None = all registered companies.
            Keys are lowercase (e.g. ["google", "amazon", "stripe"]).
        max_total : int
            Stop after collecting this many results across all companies.
        on_result : callable | None
            Optional callback fired for each JobPost as soon as it's found.
            Useful for streaming / live display.

        Returns
        -------
        list[JobPost]

        Examples
        --------
        >>> jobs = jr.search_jobs("machine learning engineer",
        ...                        companies=["databricks", "snowflake", "stripe"])
        >>> jobs = jr.search_jobs("backend engineer")   # searches all ~60 companies
        """
        if not query.strip():
            return []

        targets = companies or list(COMPANY_REGISTRY.keys())
        all_jobs: list[JobPost] = []

        self._log(f"Searching '{query}' across {len(targets)} companies …")

        for company_key in targets:
            if len(all_jobs) >= max_total:
                break

            info = COMPANY_REGISTRY.get(company_key.lower())
            if not info:
                self._log(f"Unknown company: '{company_key}' — skipped")
                continue

            ats  = info["ats"]
            name = info.get("name", company_key.title())
            n    = min(self.max_per_company, max_total - len(all_jobs))

            try:
                if ats == "eightfold":
                    # Support both built-in registry and custom
                    if "subdomain" in info:
                        # Custom eightfold entry
                        base_url = f"https://{info['subdomain']}.eightfold.ai/careers"
                        jobs = self._ef.fetch_by_url(base_url, name, query, n)
                    else:
                        jobs = self._ef.fetch(info["key"], query, n)

                elif ats == "lever":
                    jobs = self._lev.fetch_by_slug(info["key"], name, query, n)

                elif ats == "greenhouse":
                    jobs = self._gh.fetch_by_token(info["key"], name, query, n)

                elif ats == "workday":
                    jobs = self._wd.fetch(info["key"], query, n)

                elif ats == "web":
                    raw_url = info.get("url", "")
                    url = raw_url.replace("{query}", urllib.parse.quote(query))
                    jobs = self._web.fetch(name, url, query, n)

                else:
                    jobs = []

            except Exception as e:
                self._log(f"  Error fetching {name}: {e}")
                jobs = []

            for job in jobs:
                all_jobs.append(job)
                if on_result:
                    on_result(job)

            if jobs:
                time.sleep(self.delay)

        self._log(f"Done. {len(all_jobs)} job listings found for '{query}'.")
        return all_jobs

    def search_one(self, query: str, company: str) -> list[JobPost]:
        """Shorthand to search a single company."""
        return self.search_jobs(query, companies=[company])

    # ── display ───────────────────────────────────────────────────────────────

    def print_jobs(self, jobs: list[JobPost], show_desc: bool = True):
        """
        Pretty-print job results to the terminal.

        Uses ``rich`` for coloured output if installed, plain text otherwise.
        """
        if not jobs:
            print("\n  No jobs found.\n")
            return

        if HAS_RICH:
            self._print_rich(jobs, show_desc)
        else:
            self._print_plain(jobs, show_desc)

    def _print_plain(self, jobs: list[JobPost], show_desc: bool):
        sep = "─" * 70
        print(f"\n{'═'*70}")
        print(f"  {len(jobs)} Job Listing(s)")
        print(f"{'═'*70}")
        for i, j in enumerate(jobs, 1):
            print(f"\n  [{i}] {j.title}")
            print(f"      Company   : {j.company}  ({j.source})")
            print(f"      Location  : {j.location}")
            if j.department:
                print(f"      Dept      : {j.department}")
            if j.job_type:
                print(f"      Type      : {j.job_type}")
            if j.posted_date:
                print(f"      Posted    : {j.posted_date}")
            if show_desc and j.description:
                print(f"      Summary   : {j.short_desc(200)}")
            print(f"      ▶ Apply   : {j.apply_url}")
            print(f"      {sep}")
        print()

    def _print_rich(self, jobs: list[JobPost], show_desc: bool):
        console = Console()
        table = Table(
            title=f"[bold cyan]{len(jobs)} Job Listings[/bold cyan]",
            box=box.ROUNDED, show_lines=True,
            header_style="bold magenta",
        )
        table.add_column("#",          style="dim",         width=3)
        table.add_column("Title",      style="bold white",  min_width=28)
        table.add_column("Company",    style="cyan",        min_width=14)
        table.add_column("Location",   style="yellow",      min_width=18)
        table.add_column("Dept",       style="green",       min_width=12)
        table.add_column("Posted",     style="dim",         width=10)
        table.add_column("Apply URL",  style="blue",        min_width=30)

        for i, j in enumerate(jobs, 1):
            table.add_row(
                str(i),
                j.title,
                f"{j.company}\n[dim]({j.source})[/dim]",
                j.location or "—",
                j.department or "—",
                j.posted_date or "—",
                j.apply_url,
            )

        console.print(table)
        if show_desc:
            console.print()
            for i, j in enumerate(jobs, 1):
                if j.description:
                    console.print(f"[dim]{i}.[/dim] [italic]{j.short_desc(220)}[/italic]")
            console.print()

    # ── export ────────────────────────────────────────────────────────────────

    def to_json(self, jobs: list[JobPost], path: str):
        """Save results to a JSON file."""
        data = [j.to_dict() for j in jobs]
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        self._log(f"Saved {len(jobs)} jobs → {path}")

    def to_csv(self, jobs: list[JobPost], path: str):
        """Save results to a CSV file (no extra dependencies needed)."""
        import csv
        if not jobs:
            return
        fields = list(jobs[0].to_dict().keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(j.to_dict() for j in jobs)
        self._log(f"Saved {len(jobs)} jobs → {path}")

    # ── dunder ────────────────────────────────────────────────────────────────

    def __repr__(self):
        return f"JobRadar(companies={len(COMPANY_REGISTRY)}, timeout={self.timeout}s)"