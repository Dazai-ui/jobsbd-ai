import json
from typing import Iterable, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from base import JobSource
from models import NormalizedJob
from source_policy import OFFICIAL_SOURCE_PRIORITY


class JsonLdJobSource(JobSource):
    """Generic adapter for career pages exposing schema.org JobPosting JSON-LD."""

    def __init__(self, name: str, career_url: str, organization_name: str):
        self.name = name
        self.career_url = career_url
        self.organization_name = organization_name

    def _walk(self, value: Any):
        if isinstance(value, list):
            for item in value:
                yield from self._walk(item)
        elif isinstance(value, dict):
            if value.get("@type") == "JobPosting":
                yield value
            for child in value.values():
                if isinstance(child, (dict, list)):
                    yield from self._walk(child)

    @staticmethod
    def _safe_date(value):
        if not value:
            return None
        try:
            return parse_date(value)
        except Exception:
            return None

    @staticmethod
    def _location(item: dict):
        loc = item.get("jobLocation")
        if isinstance(loc, list) and loc:
            loc = loc[0]
        if isinstance(loc, dict):
            address = loc.get("address", {})
            if isinstance(address, dict):
                parts = [
                    address.get("addressLocality"),
                    address.get("addressRegion"),
                    address.get("addressCountry"),
                ]
                return ", ".join(p for p in parts if p)
        return None

    def fetch(self) -> Iterable[NormalizedJob]:
        response = requests.get(
            self.career_url,
            timeout=25,
            headers={"User-Agent": "JobsBDAggregator/0.1 (+public job discovery)"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or "")
            except Exception:
                continue

            for item in self._walk(payload):
                hiring_org = item.get("hiringOrganization") or {}
                org_name = (
                    hiring_org.get("name")
                    if isinstance(hiring_org, dict)
                    else None
                ) or self.organization_name

                source_url = item.get("url") or item.get("sameAs") or self.career_url
                source_url = urljoin(self.career_url, source_url)

                yield NormalizedJob(
                    title=item.get("title") or item.get("name") or "Untitled job",
                    organization_name=org_name,
                    source_name=self.name,
                    source_url=source_url,
                    location=self._location(item),
                    employment_type=(
                        ", ".join(item["employmentType"])
                        if isinstance(item.get("employmentType"), list)
                        else item.get("employmentType")
                    ),
                    description=BeautifulSoup(
                        item.get("description") or "", "html.parser"
                    ).get_text(" ", strip=True),
                    posted_at=self._safe_date(item.get("datePosted")),
                    deadline=self._safe_date(item.get("validThrough")),
                    source_job_id=str(item.get("identifier") or "") or None,
                    source_priority=OFFICIAL_SOURCE_PRIORITY,
                    raw_payload=item,
                )
