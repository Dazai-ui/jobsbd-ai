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
    "User-Agent": "JobsBDAggregator/0.3 (+public job discovery; respectful polling)"
}

TARGET_TITLE = re.compile(
    r"("
    r"\bai\b|artificial intelligence|machine learning|deep learning|"
    r"data science|data scientist|data analyst|data annotator|data engineer|"
    r"ml engineer|ai engineer|mlops|nlp|llm|computer vision|"
    r"lecturer|assistant lecturer|faculty member|adjunct faculty|"
    r"research assistant|teaching assistant|contractual lecturer"
    r")",
    re.I,
)


class SkillJobsSource(JobSource):
    name = "Skill.Jobs"
    listing_url = "https://skill.jobs/browse-jobs"

    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _date(text: str, kind: str):
        if kind == "deadline":
            patterns = (
                r"(?:application\s+)?deadline\s*:?\s*([^\n|]{4,60})",
                r"expiration\s+date\s*:?\s*([^\n|]{4,60})",
            )
        else:
            patterns = (
                r"(?:date\s+)?posted\s*:?\s*([^\n|]{4,60})",
                r"published\s*:?\s*([^\n|]{4,60})",
            )
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return parse_date(match.group(1), fuzzy=True)
                except Exception:
                    pass
        return None

    @staticmethod
    def _label(text: str, names: tuple[str, ...]) -> Optional[str]:
        for name in names:
            match = re.search(
                rf"(?:^|\n)\s*{re.escape(name)}\s*:?\s*([^\n]+)",
                text,
                re.I,
            )
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip(" :-")[:250]
        return None

    def _listing_jobs(self):
        soup = BeautifulSoup(self._get(self.listing_url), "html.parser")
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            absolute = urljoin(self.listing_url, href).split("#", 1)[0]
            if not re.match(r"^https://skill\.jobs/jobs/[^/?#]+/?$", absolute, re.I):
                continue
            if absolute in seen:
                continue

            title = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
            if not title or not TARGET_TITLE.search(title):
                continue

            company = None
            container = anchor
            for _ in range(5):
                container = container.parent
                if container is None:
                    break
                company_anchor = container.find(
                    "a",
                    href=re.compile(r"/company-profile/", re.I),
                )
                if company_anchor:
                    company = re.sub(
                        r"\s+", " ", company_anchor.get_text(" ", strip=True)
                    ).strip()
                    if company:
                        break

            seen.add(absolute)
            yield absolute, title, company

    def fetch(self) -> Iterable[NormalizedJob]:
        for url, listing_title, listing_company in self._listing_jobs():
            try:
                soup = BeautifulSoup(self._get(url), "html.parser")
                text = re.sub(r"\n{2,}", "\n", soup.get_text("\n", strip=True))
            except Exception:
                text = listing_title

            company = (
                self._label(text, ("Company Name", "Company"))
                or listing_company
                or "Unknown Employer"
            )

            yield NormalizedJob(
                title=listing_title,
                organization_name=company,
                source_name=self.name,
                source_url=url,
                location=self._label(text, ("Job Location", "Location")),
                employment_type=self._label(
                    text, ("Job Nature", "Job Type", "Employment Type")
                ),
                description=text,
                requirements=text,
                posted_at=self._date(text, "posted"),
                deadline=self._date(text, "deadline"),
                source_job_id=url.rstrip("/").rsplit("/", 1)[-1],
                source_priority=PORTAL_SOURCE_PRIORITY,
                raw_payload={"adapter": "skilljobs"},
            )
