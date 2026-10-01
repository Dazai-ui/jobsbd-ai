import re
from typing import Iterable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from base import JobSource
from models import NormalizedJob
from source_policy import PORTAL_SOURCE_PRIORITY


HEADERS = {
    "User-Agent": "JobsBDAggregator/0.5 (+public job discovery; respectful polling)"
}

TITLE_RE = re.compile(
    r"\b(?:"
    r"artificial intelligence|ai engineer|machine learning|ml engineer|"
    r"data scientist|data science|data analyst|data analytics|"
    r"data engineer|analytics engineer|business intelligence|"
    r"computer vision|natural language processing|\bnlp\b|"
    r"large language model|\bllm\b|generative ai|genai|mlops|"
    r"prompt engineer"
    r")\b",
    re.I,
)


class BdJobsSource(JobSource):
    name = "Bdjobs"
    listing_url = "https://jobs.bdjobs.com/jobsearch-cache.asp?fcatid=8&ln=1&pg={page}&req=mob"

    def __init__(self, timeout: int = 25, pages: int = 3):
        self.timeout = timeout
        self.pages = pages
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _job_id(href: str) -> Optional[str]:
        for pattern in (
            r"[?&]id=(\d+)",
            r"/h/details/(\d+)",
        ):
            match = re.search(pattern, href, re.I)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _relevant_title(title: str) -> bool:
        return bool(TITLE_RE.search(title))

    def _candidates(self):
        seen: set[str] = set()
        for page in range(1, self.pages + 1):
            url = self.listing_url.format(page=page)
            soup = BeautifulSoup(self._get(url), "html.parser")
            for anchor in soup.find_all("a", href=True):
                title = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
                if not title or not self._relevant_title(title):
                    continue

                absolute = urljoin(url, anchor["href"].strip())
                job_id = self._job_id(absolute)
                if not job_id or job_id in seen:
                    continue

                seen.add(job_id)
                yield job_id, title

    @staticmethod
    def _line_value(lines: list[str], labels: tuple[str, ...]) -> Optional[str]:
        lowered = [line.lower().strip(" :") for line in lines]
        for i, line in enumerate(lowered):
            for label in labels:
                label_lower = label.lower()
                if line == label_lower or line.startswith(label_lower + " "):
                    raw = lines[i]
                    inline = re.sub(
                        rf"^{re.escape(label)}\s*:?\s*",
                        "",
                        raw,
                        flags=re.I,
                    ).strip()
                    if inline and inline.lower() != label_lower:
                        return inline[:250]
                    for candidate in lines[i + 1:i + 4]:
                        value = candidate.strip(" :-")
                        if value:
                            return value[:250]
        return None

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        try:
            return parse_date(value, fuzzy=True, dayfirst=True)
        except Exception:
            return None

    @staticmethod
    def _organization(lines: list[str], title: str) -> str:
        title_lower = title.lower()
        generic = {
            "image", "share", "apply now", "requirements", "responsibilities & context",
            "employment status", "job location", "workplace", "skills & expertise",
        }

        title_index = next(
            (i for i, line in enumerate(lines) if line.lower() == title_lower),
            None,
        )
        if title_index is not None:
            for candidate in reversed(lines[max(0, title_index - 6):title_index]):
                clean = candidate.strip()
                lower = clean.lower()
                if (
                    clean
                    and lower not in generic
                    and "bdjobs" not in lower
                    and "image" not in lower
                    and not lower.startswith("published")
                ):
                    return clean[:250]

        return "Bdjobs Employer"

    def _parse_detail(self, job_id: str, listing_title: str) -> NormalizedJob:
        source_url = f"https://bdjobs.com/h/details/{job_id}"
        soup = BeautifulSoup(self._get(source_url), "html.parser")
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in soup.get_text("\n", strip=True).splitlines()
            if line.strip()
        ]
        text = "\n".join(lines)

        title = listing_title
        organization = self._organization(lines, title)
        location = self._line_value(lines, ("Job Location", "Location"))
        employment_type = self._line_value(lines, ("Employment Status",))
        deadline = self._parse_date(
            self._line_value(lines, ("Application Deadline",))
        )
        posted = self._parse_date(self._line_value(lines, ("Published",)))

        return NormalizedJob(
            title=title,
            organization_name=organization,
            source_name=self.name,
            source_url=source_url,
            location=location,
            employment_type=employment_type,
            description=text,
            requirements=text,
            posted_at=posted,
            deadline=deadline,
            source_job_id=job_id,
            source_priority=PORTAL_SOURCE_PRIORITY,
            raw_payload={"adapter": "bdjobs_it_prefilter"},
        )

    def fetch(self) -> Iterable[NormalizedJob]:
        for job_id, title in self._candidates():
            try:
                yield self._parse_detail(job_id, title)
            except Exception:
                continue
