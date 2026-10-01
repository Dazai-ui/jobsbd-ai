import re
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from base import JobSource
from models import NormalizedJob
from source_policy import PORTAL_SOURCE_PRIORITY
from sources.bdjobs_academic_source import ACADEMIC_ROLE_RE, CS_CONTEXT_RE
from sources.bdjobs_source import TITLE_RE


HEADERS = {
    "User-Agent": "JobsBDAggregator/0.6 (+public job discovery; respectful polling)"
}


class NextJobzSource(JobSource):
    name = "NextJobz"
    listing_url = "https://nextjobz.com.bd/jobs"

    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _card_text(anchor, title: str) -> str:
        node = anchor
        fallback = title
        for _ in range(8):
            node = getattr(node, "parent", None)
            if node is None:
                break
            lines = [
                re.sub(r"\s+", " ", value).strip()
                for value in node.stripped_strings
                if value.strip()
            ]
            if not lines:
                continue
            text = "\n".join(lines)
            if title.lower() not in text.lower():
                continue
            fallback = text
            if len(lines) >= 3 and len(text) <= 5000:
                return text
        return fallback

    @staticmethod
    def _relevant(title: str, context: str) -> bool:
        combined = f"{title}\n{context}"
        if TITLE_RE.search(title):
            return True
        return bool(
            ACADEMIC_ROLE_RE.search(title)
            and CS_CONTEXT_RE.search(combined)
        )

    @staticmethod
    def _extract_deadline(text: str):
        match = re.search(
            r"(?:application\s+)?deadline\s*:?\s*([^\n]{4,60})",
            text,
            re.I,
        )
        if not match:
            return None
        try:
            return parse_date(match.group(1), fuzzy=True, dayfirst=True)
        except Exception:
            return None

    @staticmethod
    def _organization(lines: list[str], title: str) -> str:
        title_lower = title.lower()
        generic = (
            "deadline", "experience", "location", "salary", "onsite",
            "on-site", "remote", "hybrid", "full-time", "part-time",
            "contractual", "internship",
        )

        title_index = next(
            (i for i, line in enumerate(lines) if line.lower() == title_lower),
            None,
        )
        if title_index is not None:
            for candidate in lines[title_index + 1:title_index + 5]:
                lower = candidate.lower()
                if (
                    candidate
                    and not any(term in lower for term in generic)
                    and not re.fullmatch(r"[\d\s,./()\-+]+", candidate)
                ):
                    return candidate[:250]
        return "NextJobz Employer"

    @staticmethod
    def _source_job_id(url: str) -> str:
        path = urlparse(url).path.strip("/")
        return path.rsplit("/", 1)[-1] or url

    def fetch(self) -> Iterable[NormalizedJob]:
        soup = BeautifulSoup(self._get(self.listing_url), "html.parser")
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            title = re.sub(
                r"\s+", " ", anchor.get_text(" ", strip=True)
            ).strip()
            if not title:
                continue

            context = self._card_text(anchor, title)
            if not self._relevant(title, context):
                continue

            source_url = urljoin(self.listing_url, anchor["href"].strip())
            parsed = urlparse(source_url)
            if parsed.netloc.lower() not in {
                "nextjobz.com.bd",
                "www.nextjobz.com.bd",
            }:
                continue
            if source_url.rstrip("/") == self.listing_url.rstrip("/"):
                continue

            source_job_id = self._source_job_id(source_url)
            if source_job_id in seen:
                continue
            seen.add(source_job_id)

            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in context.splitlines()
                if line.strip()
            ]

            yield NormalizedJob(
                title=title,
                organization_name=self._organization(lines, title),
                source_name=self.name,
                source_url=source_url,
                description=context,
                requirements=context,
                deadline=self._extract_deadline(context),
                source_job_id=source_job_id,
                source_priority=PORTAL_SOURCE_PRIORITY,
                raw_payload={"adapter": "nextjobz_public_listing"},
            )
