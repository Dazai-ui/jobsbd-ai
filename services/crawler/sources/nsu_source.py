import re
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from base import JobSource
from models import NormalizedJob


HEADERS = {
    "User-Agent": "JobsBDAggregator/0.3 (+public job discovery; respectful polling)"
}

ROLE_PATTERNS = {
    "Assistant Lecturer": r"\bassistant\s+lecturer\b",
    "Research Assistant": r"\b(?:graduate\s+)?research\s+assistant\b",
    "Teaching Assistant": r"\b(?:graduate\s+)?teaching\s+assistant\b",
    "Adjunct Lecturer": r"\badjunct\s+lecturer\b",
    "Adjunct Faculty": r"\badjunct\s+faculty\b",
    "Contractual Lecturer": r"\b(?:contractual|contract)\s+lecturer\b",
    "Faculty Member": r"\bfaculty\s+member\b",
}

PLAIN_LECTURER = re.compile(
    r"(?<!senior\s)(?<!assistant\s)(?<!adjunct\s)(?<!visiting\s)\blecturer\b",
    re.I,
)


class NsuFacultySource(JobSource):
    name = "NSU Careers"
    organization_name = "North South University (NSU)"
    listing_url = "https://jobs.northsouth.edu/"

    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def _detail_urls(self) -> list[str]:
        soup = BeautifulSoup(self._get(self.listing_url), "html.parser")
        urls: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            absolute = urljoin(self.listing_url, anchor["href"].strip()).split("#", 1)[0]
            if re.match(r"^https://jobs\.northsouth\.edu/job/\d+/?$", absolute, re.I):
                urls.add(absolute)
        return sorted(urls)

    @staticmethod
    def _parse_date(text: str, label_pattern: str):
        match = re.search(label_pattern, text, re.I)
        if not match:
            return None
        try:
            return parse_date(match.group(1), fuzzy=True)
        except Exception:
            return None

    @staticmethod
    def _roles(text: str) -> list[str]:
        flat = re.sub(r"\s+", " ", text)
        roles = [
            display
            for display, pattern in ROLE_PATTERNS.items()
            if re.search(pattern, flat, re.I)
        ]
        if PLAIN_LECTURER.search(flat):
            roles.append("Lecturer")
        return list(dict.fromkeys(roles))

    @staticmethod
    def _title(soup: BeautifulSoup) -> str:
        for node in soup.select("h2, h1"):
            value = node.get_text(" ", strip=True)
            if value:
                return value
        return "Faculty Recruitment"

    @staticmethod
    def _slug(url: str) -> str:
        return urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]

    def fetch(self) -> Iterable[NormalizedJob]:
        for url in self._detail_urls():
            soup = BeautifulSoup(self._get(url), "html.parser")
            text = soup.get_text("\n", strip=True)
            title = self._title(soup)
            roles = self._roles(text)

            if not roles:
                continue

            deadline = self._parse_date(
                text,
                r"application\s+deadline\s*:?\s*([^\n]{4,60})",
            )
            posted = self._parse_date(
                text,
                r"date\s+posted\s*:?\s*([^\n]{4,60})",
            )

            for role in roles:
                yield NormalizedJob(
                    title=f"{role} – {title}",
                    organization_name=self.organization_name,
                    source_name=self.name,
                    source_url=url,
                    location="Dhaka",
                    employment_type="Full Time",
                    description=f"Official NSU recruitment notice. Entry-level academic role detected: {role}.",
                    requirements=f"See the official NSU circular for {role} requirements.",
                    posted_at=posted,
                    deadline=deadline,
                    source_job_id=f"{self._slug(url)}:{role.lower().replace(' ', '-')}",
                    raw_payload={
                        "adapter": "nsu_bundled_academic",
                        "notice_title": title,
                    },
                )
