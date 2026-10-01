import re
from typing import Iterable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from base import JobSource
from models import NormalizedJob
from source_policy import PORTAL_SOURCE_PRIORITY
from sources.bdjobs_source import TITLE_RE


HEADERS = {
    "User-Agent": "JobsBDAggregator/0.5 (+public job discovery; respectful polling)"
}


class JobComBdSource(JobSource):
    name = "Job.com.bd"
    listing_url = "https://job.com.bd/jobs/?c=10"

    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _job_id(href: str) -> Optional[str]:
        match = re.search(r"[?&]i=(\d+)", href)
        return match.group(1) if match else None

    def _candidates(self):
        soup = BeautifulSoup(self._get(self.listing_url), "html.parser")
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            title = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
            if not title or not TITLE_RE.search(title):
                continue

            absolute = urljoin(self.listing_url, anchor["href"].strip())
            job_id = self._job_id(absolute)
            if not job_id or job_id in seen:
                continue

            seen.add(job_id)
            yield job_id, title, absolute

    @staticmethod
    def _extract(text: str, label: str) -> Optional[str]:
        match = re.search(
            rf"(?:^|\n)\s*{re.escape(label)}\s*:?\s*([^\n]+)",
            text,
            re.I,
        )
        if not match:
            return None
        value = re.sub(r"\s+", " ", match.group(1)).strip(" :-")
        return value[:250] if value else None

    @staticmethod
    def _date(value: Optional[str]):
        if not value:
            return None
        try:
            return parse_date(value, fuzzy=True, dayfirst=True)
        except Exception:
            return None

    def _parse_detail(self, job_id: str, title: str, source_url: str) -> NormalizedJob:
        soup = BeautifulSoup(self._get(source_url), "html.parser")
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in soup.get_text("\n", strip=True).splitlines()
            if line.strip()
        ]
        text = "\n".join(lines)

        title_index = next(
            (i for i, line in enumerate(lines) if title.lower() in line.lower()),
            None,
        )
        organization = "Job.com.bd Employer"
        if title_index is not None:
            for candidate in reversed(lines[max(0, title_index - 8):title_index]):
                lower = candidate.lower()
                if (
                    candidate
                    and "published" not in lower
                    and "application deadline" not in lower
                    and "job.com.bd" not in lower
                ):
                    organization = candidate[:250]
                    break

        return NormalizedJob(
            title=title,
            organization_name=organization,
            source_name=self.name,
            source_url=source_url,
            location=self._extract(text, "Job Location"),
            employment_type=self._extract(text, "Employment Type"),
            description=text,
            requirements=text,
            posted_at=self._date(self._extract(text, "Published on")),
            deadline=self._date(self._extract(text, "Application Deadline")),
            source_job_id=job_id,
            source_priority=PORTAL_SOURCE_PRIORITY,
            raw_payload={"adapter": "job_com_bd_it_prefilter"},
        )

    def fetch(self) -> Iterable[NormalizedJob]:
        for job_id, title, source_url in self._candidates():
            try:
                yield self._parse_detail(job_id, title, source_url)
            except Exception:
                continue
