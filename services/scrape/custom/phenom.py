from __future__ import annotations

import json
import re
from typing import Any, List
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from data.model import Job
from services.scrape.http_client import get_http


class PhenomAdapter:
    pattern = re.compile(r"(?:^|\.)careers\.gene\.com$", re.I)
    renders = False
    name = "phenom"

    @staticmethod
    def matches(url: str) -> bool:
        return bool(PhenomAdapter.pattern.search(urlparse(url).netloc))

    @staticmethod
    async def scrape(url: str, *, timeout: int = 20, max_pages: int = 5) -> List[Job]:
        jobs: List[Job] = []
        seen: set[str] = set()
        next_url = url
        page_size: int | None = None

        for page_idx in range(max_pages):
            http = await get_http()
            html = await http.fetch_text(next_url)
            payload = _extract_ddo(html)
            page_jobs = _jobs_from_payload(payload)
            if not page_jobs:
                break

            for item in page_jobs:
                title = str(item.get("title") or "").strip()
                link = str(item.get("applyUrl") or "").strip()
                if not title or not link or link in seen:
                    continue
                seen.add(link)
                jobs.append(Job(title=title, link=link))

            page_size = page_size or len(page_jobs)
            total = _total_hits(payload)
            if total is not None and len(jobs) >= total:
                break
            if not page_size:
                break
            next_url = _with_from(url, (page_idx + 1) * page_size)

        return jobs


def _extract_ddo(html: str) -> dict[str, Any]:
    m = re.search(r"phApp\.ddo\s*=\s*", html)
    if not m:
        return {}
    raw = _balanced_object(html, m.end())
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _balanced_object(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escaped = False

    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]

    return ""


def _jobs_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("eagerLoadRefineSearch", {}).get("data", {})
    jobs = data.get("jobs", [])
    return jobs if isinstance(jobs, list) else []


def _total_hits(payload: dict[str, Any]) -> int | None:
    value = payload.get("eagerLoadRefineSearch", {}).get("totalHits")
    return value if isinstance(value, int) else None


def _with_from(url: str, offset: int) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["from"] = [str(offset)]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
