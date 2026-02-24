"""
portals.py — Portal loading, domain matching, and career page scraping.
"""

import json
import os
import concurrent.futures
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import DOMAIN_TO_COMPANIES, SCRAPE_HEADERS, ROLE_KEYWORDS   # direct import

_JOB_SELECTORS = [
    {"card":"[class*='job-card']",   "title":"[class*='title']", "link":"a"},
    {"card":"[class*='job-item']",   "title":"[class*='title']", "link":"a"},
    {"card":"[class*='job-listing']","title":"h2,h3,h4",         "link":"a"},
    {"card":"[class*='position']",   "title":"h2,h3,h4",         "link":"a"},
    {"card":"[class*='opening']",    "title":"h2,h3,h4",         "link":"a"},
    {"card":"li[class*='job']",      "title":"h2,h3,h4,span,a",  "link":"a"},
    {"card":".posting",              "title":"h5,.posting-title", "link":"a[href]"},
    {"card":".job",                  "title":"h3,h4,.job-title",  "link":"a"},
]


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


def load_portals(json_path: str = None) -> list:
    """Load Portal.json from the backend folder or provided path."""
    candidates = [
        json_path,
        os.path.join(os.path.dirname(__file__), "Portal__1_.json"),
        os.path.join(os.path.dirname(__file__), "Portal.json"),
        "/mnt/user-data/uploads/Portal__1_.json",
        "Portal__1_.json",
        "Portal.json",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            with open(path) as f:
                raw = json.load(f)
            portals = []
            for item in raw:
                link = item["Link"].strip()
                if not link.startswith("http"):
                    link = "https://" + link
                portals.append({"title": item["Title"].strip(), "link": link})
            return portals
    return []


def get_relevant_portals(domains: list, skills: list, portals: list, limit: int = 8) -> list:
    """Return portals most relevant to the candidate's domains/skills."""
    wanted = set()
    for d in domains:
        for c in DOMAIN_TO_COMPANIES.get(d, []):
            wanted.add(c.lower())
    if not wanted:
        for companies in DOMAIN_TO_COMPANIES.values():
            for c in companies:
                wanted.add(c.lower())

    matched, seen = [], set()
    for p in portals:
        pt = p["title"].lower()
        if any(frag in pt or pt in frag for frag in wanted) and pt not in seen:
            matched.append(p); seen.add(pt)
        if len(matched) >= limit:
            break
    for p in portals:
        if len(matched) >= limit:
            break
        if p["title"].lower() not in seen:
            matched.append(p); seen.add(p["title"].lower())
    return matched[:limit]


def _scrape_one_portal(portal: dict, search_terms: list, timeout: int = 8) -> list:
    company, base_url, jobs = portal["title"], portal["link"], []
    try:
        r = requests.get(base_url, headers=SCRAPE_HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code not in (200, 201):
            return []
        soup = BeautifulSoup(r.text, "html.parser")

        for sel in _JOB_SELECTORS:
            cards = soup.select(sel["card"])
            if not cards:
                continue
            for card in cards[:30]:
                title_el = card if sel["title"] == "self" else card.select_one(sel["title"])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not _is_job_title(title):
                    continue
                link_el = card.select_one(sel["link"]) if sel["link"] != "a" else card.find("a")
                href = _resolve_href(link_el["href"], base_url) if (link_el and link_el.get("href")) else base_url
                jobs.append({"source":"Career Page","company":company,"title":title,
                             "location":"Check career page",
                             "description":card.get_text(separator=" ",strip=True)[:200],
                             "url":href,"salary":None})
            if jobs:
                break

        if not jobs:
            seen_titles = set()
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                if not _is_job_title(text) or text in seen_titles:
                    continue
                seen_titles.add(text)
                jobs.append({"source":"Career Page","company":company,"title":text,
                             "location":"Check career page","description":"",
                             "url":_resolve_href(a["href"], base_url),"salary":None})
    except Exception:
        pass

    if jobs and search_terms:
        terms_lower = [t.lower() for t in search_terms]
        filtered = [j for j in jobs if any(t in j["title"].lower() for t in terms_lower)
                    or any(kw in j["title"].lower() for kw in ROLE_KEYWORDS)]
        jobs = filtered or jobs[:3]
    return jobs[:5]


def scrape_portal_jobs(portals: list, search_terms: list, max_workers: int = 6) -> list:
    """Scrape multiple career pages in parallel."""
    all_jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_scrape_one_portal, p, search_terms): p for p in portals}
        for future in concurrent.futures.as_completed(futures, timeout=20):
            try:
                all_jobs.extend(future.result())
            except Exception:
                pass
    return all_jobs
