"""Job sources. Only uses public/official APIs (no scraping of LinkedIn/Naukri,
which forbid automation in their terms and ban accounts that do it).

NOTE: verify each API's current response format before relying on it; these
endpoints can change.
"""
from __future__ import annotations

import hashlib
import html
import os
import re
from dataclasses import dataclass

import requests

TIMEOUT = 20


@dataclass
class Job:
    id: str
    source: str
    title: str
    company: str
    location: str
    url: str
    description: str


def _clean(text: str | None) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _make_id(source: str, raw_id: str, url: str) -> str:
    key = f"{source}:{raw_id or url}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def fetch_remotive(query: str) -> list[Job]:
    """Remote jobs. https://remotive.com/api/remote-jobs?search=<q>"""
    r = requests.get(
        "https://remotive.com/api/remote-jobs",
        params={"search": query},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    jobs = []
    for j in r.json().get("jobs", []):
        jobs.append(
            Job(
                id=_make_id("remotive", str(j.get("id", "")), j.get("url", "")),
                source="remotive",
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                location=j.get("candidate_required_location", "Remote"),
                url=j.get("url", ""),
                description=_clean(j.get("description")),
            )
        )
    return jobs


def fetch_adzuna(query: str, where: str, country: str = "in") -> list[Job]:
    """Adzuna search API (free key). Skipped if no credentials are set."""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []
    r = requests.get(
        f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
        params={
            "app_id": app_id,
            "app_key": app_key,
            "what": query,
            "where": where,
            "results_per_page": 20,
            "content-type": "application/json",
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    jobs = []
    for j in r.json().get("results", []):
        url = j.get("redirect_url", "")
        jobs.append(
            Job(
                id=_make_id("adzuna", str(j.get("id", "")), url),
                source="adzuna",
                title=_clean(j.get("title")),
                company=(j.get("company") or {}).get("display_name", ""),
                location=(j.get("location") or {}).get("display_name", ""),
                url=url,
                description=_clean(j.get("description")),
            )
        )
    return jobs


def fetch_all(cfg: dict) -> list[Job]:
    jobs: list[Job] = []
    for q in cfg.get("remote_queries", []):
        try:
            jobs += fetch_remotive(q)
        except Exception as e:  # keep going if one source fails
            print(f"[warn] remotive '{q}' failed: {e}")
    for s in cfg.get("searches", []):
        try:
            jobs += fetch_adzuna(s["query"], s.get("where", "India"))
        except Exception as e:
            print(f"[warn] adzuna '{s}' failed: {e}")

    seen, unique = set(), []
    for j in jobs:
        if j.id not in seen:
            seen.add(j.id)
            unique.append(j)
    return unique
