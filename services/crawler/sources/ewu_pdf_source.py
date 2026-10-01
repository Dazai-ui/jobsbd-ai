from sources.aiub_pdf_source import AiubFacultyPdfSource


class EwuAcademicPdfSource(AiubFacultyPdfSource):
    name = "EWU Careers"
    organization_name = "East West University (EWU)"
    listing_url = "https://www.ewubd.edu/career-archive"
    short_name = "EWU"
    adapter_name = "ewu_academic_pdf"
