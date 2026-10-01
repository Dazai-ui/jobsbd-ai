import re
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from base import JobSource
from models import NormalizedJob


DEFAULT_HEADERS = {
    "User-Agent": "JobsBDAggregator/0.2 (+public job discovery; respectful polling)"
}


class HtmlDetailSource(JobSource):
    """Generic source for career listing pages that link to detail pages.

    The adapter intentionally relies on resilient text extraction rather than
    site-specific DOM classes. Source-specific URL patterns decide which links
    are treated as jobs.
    """

    def __init__(
        self,
        *,
        name: str,
        organization_name: str,
        listing_urls: list[str],
        detail_url_regex: str,
        timeout: int = 25,
    ):
        self.name = name
        self.organization_name = organization_name
        self.listing_urls = listing_urls
        self.detail_url_re = re.compile(detail_url_regex, re.I)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def _detail_urls(self) -> list[str]:
        urls: set[str] = set()
        for listing_url in self.listing_urls:
            soup = BeautifulSoup(self._get(listing_url), "html.parser")
            for anchor in soup.find_all("a", href=True):
                absolute = urljoin(listing_url, anchor["href"].strip())
                absolute = absolute.split("#", 1)[0]
                if self.detail_url_re.match(absolute):
                    urls.add(absolute)
        return sorted(urls)

    @staticmethod
    def _first_heading(soup: BeautifulSoup) -> Optional[str]:
        generic = {
            "careers at uiu", "career", "careers", "job openings",
            "open positions", "apply for this position",
        }
        for selector in ("h1", "main h2", "article h2", "h2"):
            for node in soup.select(selector):
                text = node.get_text(" ", strip=True)
                if text and text.lower() not in generic:
                    return text
        return None

    @staticmethod
    def _extract_label(text: str, labels: tuple[str, ...]) -> Optional[str]:
        for label in labels:
            pattern = rf"(?:^|\n)\s*{re.escape(label)}\s*:?\s*([^\n]+)"
            match = re.search(pattern, text, re.I)
            if match:
                value = re.sub(r"\s+", " ", match.group(1)).strip(" :-")
                if value:
                    return value[:250]
        return None

    @staticmethod
    def _extract_deadline(text: str):
        patterns = [
            r"(?:application\s+)?deadline\s*:?\s*([^\n|]{4,60})",
            r"accepting applications till\s+([^\n.]{4,60})",
            r"apply(?:\s+online)?\s+by\s+([^\n.]{4,60})",
            r"applications?\s+(?:will be accepted|are accepted)\s+(?:until|till)\s+([^\n.]{4,60})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if not match:
                continue
            candidate = match.group(1).strip(" :-,.;")
            try:
                return parse_date(candidate, fuzzy=True, dayfirst=False)
            except Exception:
                pass
        return None

    @staticmethod
    def _extract_posted(text: str):
        patterns = [
            r"posted\s*:?\s*([^\n|]{4,40})",
            r"published\s*:?\s*([^\n|]{4,40})",
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
    def _source_job_id(url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        return path.rsplit("/", 1)[-1]

    def _parse_detail(self, url: str) -> Optional[NormalizedJob]:
        soup = BeautifulSoup(self._get(url), "html.parser")
        title = self._first_heading(soup)
        if not title:
            return None

        text = soup.get_text("\n", strip=True)
        compact = re.sub(r"\n{2,}", "\n", text)

        # Detail pages may append lists of other vacancies. Feeding those
        # titles into classification can create false positives.
        for marker in (
            "\nAvailable Jobs at ",
            "\nOur Office\n",
            "\nContact & Location",
            "\nPerks & Benefits\n",
        ):
            if marker in compact:
                compact = compact.split(marker, 1)[0]

        location = self._extract_label(compact, ("Job Location", "Location"))
        employment_type = self._extract_label(compact, ("Job Type", "Employment Type"))
        department = self._extract_label(
            compact, ("Office", "Department", "Job Category", "Category")
        )

        return NormalizedJob(
            title=title,
            organization_name=self.organization_name,
            source_name=self.name,
            source_url=url,
            department=department,
            location=location,
            employment_type=employment_type,
            description=compact,
            requirements=compact,
            posted_at=self._extract_posted(compact),
            deadline=self._extract_deadline(compact),
            source_job_id=self._source_job_id(url),
            raw_payload={"adapter": "html_detail_source"},
        )

    def fetch(self) -> Iterable[NormalizedJob]:
        for url in self._detail_urls():
            job = self._parse_detail(url)
            if job is not None:
                yield job
