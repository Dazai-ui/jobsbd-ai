import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from sources.bdjobs_source import BdJobsSource


ACADEMIC_ROLE_RE = re.compile(
    r"\b(?:assistant\s+lecturer|lecturer|adjunct\s+(?:lecturer|faculty)|"
    r"faculty\s+member|research\s+assistant|teaching\s+assistant|"
    r"part[-\s]?time\s+lecturer|visiting\s+(?:lecturer|faculty)|"
    r"contract(?:ual)?\s+(?:lecturer|faculty))\b",
    re.I,
)

CS_CONTEXT_RE = re.compile(
    r"\b(?:cse|computer\s+science(?:\s*(?:&|and)\s*engineering)?|"
    r"computer\s+engineering|software\s+engineering|"
    r"information\s+technology|ict|information\s+(?:and\s+)?communication\s+technology|"
    r"data\s+science|artificial\s+intelligence|ai\s*(?:&|and)\s*data\s+science|"
    r"cyber\s*security|cybersecurity|informatics|computing)\b",
    re.I,
)


class BdJobsAcademicSource(BdJobsSource):
    name = "Bdjobs Academic"
    listing_url = (
        "https://jobs.bdjobs.com/jobsearch-cache.asp?"
        "fcatid=4&ln=1&pg={page}&req=mob"
    )

    def _candidates(self):
        seen: set[str] = set()

        for page in range(1, self.pages + 1):
            url = self.listing_url.format(page=page)
            soup = BeautifulSoup(self._get(url), "html.parser")

            for anchor in soup.find_all("a", href=True):
                title = re.sub(
                    r"\s+", " ", anchor.get_text(" ", strip=True)
                ).strip()
                if not title or not ACADEMIC_ROLE_RE.search(title):
                    continue

                absolute = urljoin(url, anchor["href"].strip())
                job_id = self._job_id(absolute)
                if not job_id or job_id in seen:
                    continue

                context = self._card_text(anchor, title)
                if not CS_CONTEXT_RE.search(f"{title}\n{context}"):
                    continue

                seen.add(job_id)
                yield job_id, title, context
