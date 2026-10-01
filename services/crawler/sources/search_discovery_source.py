import re
import xml.etree.ElementTree as ET
from typing import Iterable
from urllib.parse import urlencode, urlparse

import requests

from base import JobSource
from models import NormalizedJob
from source_policy import DISCOVERY_SOURCE_PRIORITY


HEADERS = {
    "User-Agent": "JobsBDAggregator/0.7 (+personal public job discovery; respectful polling)"
}

QUERIES = (
    'site:linkedin.com/jobs/view ("machine learning engineer" OR "ai engineer" OR "data scientist") Bangladesh',
    'site:linkedin.com/jobs/view ("data analyst" OR "computer vision" OR "nlp engineer" OR "llm engineer") Bangladesh',
    'site:linkedin.com/jobs/view ("lecturer cse" OR "lecturer computer science" OR "research assistant cse") Bangladesh',
    'site:facebook.com ("lecturer cse" OR "machine learning engineer" OR "data scientist") Bangladesh job',
)

LINKEDIN_PATTERNS = (
    re.compile(r"^(?P<company>.+?)\s+hiring\s+(?P<title>.+?)\s+in\s+.+?\s*\|\s*LinkedIn$", re.I),
    re.compile(r"^(?P<title>.+?)\s+at\s+(?P<company>.+?)\s*\|\s*LinkedIn$", re.I),
)


class SearchDiscoverySource(JobSource):
    name = "Search Discovery"
    acquisition_strategy = "search"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    @staticmethod
    def _parse_identity(result_title: str, url: str) -> tuple[str, str]:
        clean = re.sub(r"\s+", " ", result_title).strip()

        for pattern in LINKEDIN_PATTERNS:
            match = pattern.match(clean)
            if match:
                return (
                    match.group("title").strip(),
                    match.group("company").strip(),
                )

        if clean.lower().endswith("| linkedin"):
            clean = clean.rsplit("|", 1)[0].strip()

        host = urlparse(url).netloc.lower()
        company = "LinkedIn discovery" if "linkedin.com" in host else "Facebook discovery"
        return clean[:250], company

    @staticmethod
    def _allowed_url(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()

        if host.endswith("linkedin.com"):
            return "/jobs/view/" in path

        if host.endswith("facebook.com") or host.endswith("www.facebook.com"):
            return True

        return False

    def _search(self, query: str):
        params = urlencode({"q": query, "format": "rss"})
        url = f"https://www.bing.com/search?{params}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            if title and link:
                yield title, link, description

    def fetch(self) -> Iterable[NormalizedJob]:
        seen: set[str] = set()

        for query in QUERIES:
            for result_title, url, snippet in self._search(query):
                if not self._allowed_url(url) or url in seen:
                    continue

                seen.add(url)
                title, company = self._parse_identity(result_title, url)
                text = re.sub(r"<[^>]+>", " ", snippet)
                text = re.sub(r"\s+", " ", text).strip()

                yield NormalizedJob(
                    title=title,
                    organization_name=company,
                    source_name=self.name,
                    source_url=url,
                    description=text,
                    requirements=text,
                    source_job_id=url,
                    source_priority=DISCOVERY_SOURCE_PRIORITY,
                    raw_payload={
                        "adapter": "bing_rss_search_discovery",
                        "query": query,
                    },
                )
