from urllib.parse import urlparse

from sources.aiub_pdf_source import AiubFacultyPdfSource


class EwuAcademicPdfSource(AiubFacultyPdfSource):
    name = "EWU Careers"
    organization_name = "East West University (EWU)"
    listing_url = "https://www.ewubd.edu/career-archive"
    short_name = "EWU"
    adapter_name = "ewu_academic_pdf"

    @staticmethod
    def _is_candidate_pdf(url: str, label: str) -> bool:
        path = urlparse(url).path.lower()

        # The EWU career archive page also links site-wide policy PDFs.
        # They can contain words such as "faculty" but are not vacancies.
        if "/policies/" in path or "/policy/" in path:
            return False

        text = f"{label} {path}".lower()
        career_terms = (
            "career",
            "vacancy",
            "faculty",
            "lecturer",
            "research assistant",
            "teaching assistant",
            "recruit",
            "job",
            "position",
        )
        return "/storage/app/uploads/public/" in path or any(
            term in text for term in career_terms
        )

    def _pdf_links(self):
        for url, label in super()._pdf_links():
            if self._is_candidate_pdf(url, label):
                yield url, label
