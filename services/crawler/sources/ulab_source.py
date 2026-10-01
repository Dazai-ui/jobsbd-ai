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

ENTRY_POSITIONS = {
    "lecturer",
    "assistant lecturer",
    "faculty member",
    "research assistant",
    "teaching assistant",
    "adjunct lecturer",
    "adjunct faculty",
    "contractual lecturer",
    "contractual faculty",
    "part-time lecturer",
    "part time lecturer",
    "visiting lecturer",
    "visiting faculty",
}


class UlabFacultySource(JobSource):
    name = "ULAB Careers"
    organization_name = "University of Liberal Arts Bangladesh (ULAB)"
    listing_url = "https://hr.ulab.edu.bd/jobs-at-ulab"

    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def _notice_urls(self) -> list[str]:
        soup = BeautifulSoup(self._get(self.listing_url), "html.parser")
        urls: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            absolute = urljoin(self.listing_url, anchor["href"].strip()).split("#", 1)[0]
            if re.match(r"^https://hr\.ulab\.edu\.bd/jobs-ulab/[^/]+/?$", absolute, re.I):
                urls.add(absolute)
        return sorted(urls)

    @staticmethod
    def _deadline(text: str):
        match = re.search(
            r"application\s+(?:deadline|dateline)\s*:?\s*([^\n]{4,70})",
            text,
            re.I,
        )
        if not match:
            return None
        try:
            return parse_date(match.group(1), fuzzy=True)
        except Exception:
            return None

    @staticmethod
    def _header_index(headers: list[str], keywords: tuple[str, ...]):
        for i, header in enumerate(headers):
            lower = header.lower()
            if any(keyword in lower for keyword in keywords):
                return i
        return None

    @staticmethod
    def _slug(url: str) -> str:
        return urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]

    def _rows(self, soup: BeautifulSoup):
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            headers = [
                cell.get_text(" ", strip=True)
                for cell in rows[0].find_all(["th", "td"])
            ]
            position_idx = self._header_index(headers, ("position",))
            dept_idx = self._header_index(headers, ("department", "school", "center", "office"))
            area_idx = self._header_index(headers, ("area", "discipline", "subject"))

            if position_idx is None:
                continue

            for row in rows[1:]:
                cells = [
                    cell.get_text(" ", strip=True)
                    for cell in row.find_all(["th", "td"])
                ]
                if position_idx >= len(cells):
                    continue

                position = re.sub(r"\s+", " ", cells[position_idx]).strip()
                if position.lower() not in ENTRY_POSITIONS:
                    continue

                department = (
                    cells[dept_idx].strip()
                    if dept_idx is not None and dept_idx < len(cells)
                    else None
                )
                area = (
                    cells[area_idx].strip()
                    if area_idx is not None and area_idx < len(cells)
                    else None
                )
                yield position, department, area

    def fetch(self) -> Iterable[NormalizedJob]:
        for url in self._notice_urls():
            soup = BeautifulSoup(self._get(url), "html.parser")
            text = soup.get_text("\n", strip=True)
            deadline = self._deadline(text)
            notice_slug = self._slug(url)

            for position, department, area in self._rows(soup):
                summary = " | ".join(
                    part for part in (position, department, area) if part
                )
                yield NormalizedJob(
                    title=position,
                    organization_name=self.organization_name,
                    source_name=self.name,
                    source_url=url,
                    department=department,
                    location="Dhaka",
                    description=summary,
                    requirements=summary,
                    job_category=area,
                    deadline=deadline,
                    source_job_id=f"{notice_slug}:{position}:{department or ''}:{area or ''}",
                    raw_payload={
                        "adapter": "ulab_table",
                        "notice_url": url,
                        "area": area,
                    },
                )
