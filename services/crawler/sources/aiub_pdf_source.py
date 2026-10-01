import io
import re
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from pypdf import PdfReader

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


class AiubFacultyPdfSource(JobSource):
    name = "AIUB Careers"
    organization_name = "American International University-Bangladesh (AIUB)"
    listing_url = "https://www.aiub.edu/about/career"
    short_name = "AIUB"
    adapter_name = "academic_pdf"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str):
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _pdf_links(self):
        soup = BeautifulSoup(self._get(self.listing_url).text, "html.parser")
        for anchor in soup.find_all("a", href=True):
            absolute = urljoin(self.listing_url, anchor["href"].strip()).split("#", 1)[0]
            if not urlparse(absolute).path.lower().endswith(".pdf"):
                continue
            label = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
            yield absolute, label

    def _pdf_text(self, url: str) -> str:
        response = self._get(url)
        reader = PdfReader(io.BytesIO(response.content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

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
    def _date(text: str, kind: str):
        if kind == "deadline":
            patterns = [
                r"(?:application\s+)?(?:deadline|dateline)\s*:?\s*([^\n\]]{4,70})",
                r"\[Deadline:\s*([^\]]+)\]",
            ]
        else:
            patterns = [
                r"\[Posted:\s*([^\]]+)\]",
                r"(?:date\s+)?posted\s*:?\s*([^\n\]]{4,70})",
            ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return parse_date(match.group(1), fuzzy=True)
                except Exception:
                    pass
        return None

    @staticmethod
    def _slug(url: str) -> str:
        return urlparse(url).path.rsplit("/", 1)[-1].rsplit(".", 1)[0]

    @staticmethod
    def _expired(value) -> bool:
        if value is None:
            return False
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.date() < datetime.now(timezone.utc).date()

    def fetch(self) -> Iterable[NormalizedJob]:
        for pdf_url, label in self._pdf_links():
            label_deadline = self._date(label, "deadline")
            if self._expired(label_deadline):
                continue

            try:
                pdf_text = self._pdf_text(pdf_url)
            except Exception:
                continue

            roles = self._roles(pdf_text)
            if not roles:
                continue

            deadline = label_deadline or self._date(label + "\n" + pdf_text, "deadline")
            posted = self._date(label + "\n" + pdf_text, "posted")
            slug = self._slug(pdf_url)

            for role in roles:
                yield NormalizedJob(
                    title=f"{role} – {self.short_name} Faculty Search",
                    organization_name=self.organization_name,
                    source_name=self.name,
                    source_url=pdf_url,
                    location="Dhaka",
                    description=(
                        f"Official {self.short_name} academic circular. "
                        f"Entry-level academic role detected: {role}."
                    ),
                    requirements=(
                        f"See the linked {self.short_name} circular for "
                        f"the full {role} requirements."
                    ),
                    posted_at=posted,
                    deadline=deadline,
                    source_job_id=f"{slug}:{role.lower().replace(' ', '-')}",
                    raw_payload={
                        "adapter": self.adapter_name,
                        "listing_label": label,
                    },
                )
