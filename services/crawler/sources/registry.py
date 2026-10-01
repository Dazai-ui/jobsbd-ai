from sources.aiub_pdf_source import AiubFacultyPdfSource
from sources.bdjobs_source import BdJobsSource
from sources.bdjobs_academic_source import BdJobsAcademicSource
from sources.demo_source import DemoSource
from sources.ewu_pdf_source import EwuAcademicPdfSource
from sources.html_detail_source import HtmlDetailSource
from sources.jobcombd_source import JobComBdSource
from sources.nsu_source import NsuFacultySource
from sources.nextjobz_source import NextJobzSource
from sources.search_discovery_source import SearchDiscoverySource
from sources.ulab_source import UlabFacultySource


AI_DATA_TITLE_FILTER = (
    r"\b(?:artificial intelligence|ai|machine learning|ml|data|analytics|"
    r"computer vision|nlp|llm|generative ai|genai|mlops|prompt)\b"
)


def build_sources(include_demo: bool = False):
    sources = [
        HtmlDetailSource(
            name="UIU Careers",
            organization_name="United International University (UIU)",
            listing_urls=["https://www.uiu.ac.bd/career/"],
            detail_url_regex=r"^https://www\.uiu\.ac\.bd/career/(?!page/)(?!$)[^/]+/?$",
        ),
        NsuFacultySource(),
        UlabFacultySource(),
        AiubFacultyPdfSource(),
        EwuAcademicPdfSource(),
        HtmlDetailSource(
            name="University of Dhaka Jobs",
            organization_name="University of Dhaka",
            listing_urls=["https://jobs.du.ac.bd/"],
            detail_url_regex=r"^https://jobs\.du\.ac\.bd/job_details/\d+/?$",
        ),

        # Official technology-company career pages.
        HtmlDetailSource(
            name="Brain Station 23 Careers",
            organization_name="Brain Station 23",
            listing_urls=["https://brainstation-23.easy.jobs/"],
            detail_url_regex=r"^https://brainstation-23\.easy\.jobs/[a-z0-9][a-z0-9-]+/?$",
            link_text_regex=AI_DATA_TITLE_FILTER,
        ),
        HtmlDetailSource(
            name="Enosis Solutions Careers",
            organization_name="Enosis Solutions",
            listing_urls=["https://careers.enosisbd.com/"],
            detail_url_regex=r"^https://careers\.enosisbd\.com/(?:en/)?postings/[0-9a-f-]+/?$",
            link_text_regex=AI_DATA_TITLE_FILTER,
        ),
        HtmlDetailSource(
            name="Therap BD Careers",
            organization_name="Therap (BD) Ltd.",
            listing_urls=["https://therap.hire.trakstar.com/"],
            detail_url_regex=r"^https://therap\.hire\.trakstar\.com/jobs/[a-z0-9]+/?$",
            link_text_regex=AI_DATA_TITLE_FILTER,
        ),
        HtmlDetailSource(
            name="Optimizely Careers",
            organization_name="Optimizely",
            listing_urls=["https://careers.optimizely.com/viewalljobs/"],
            detail_url_regex=r"^https://careers\.optimizely\.com/job/[^/]+/\d+/?$",
            link_text_regex=AI_DATA_TITLE_FILTER,
        ),
        HtmlDetailSource(
            name="DataSoft Careers",
            organization_name="DataSoft Systems Bangladesh Ltd.",
            listing_urls=["https://datasoft-bd.com/career"],
            detail_url_regex=r"^https://datasoft-bd\.com/career-detail/[^/?#]+/?$",
            link_text_regex=AI_DATA_TITLE_FILTER,
        ),
        HtmlDetailSource(
            name="Pathao Careers",
            organization_name="Pathao",
            listing_urls=["https://careers.pathao.com/job-openings/"],
            detail_url_regex=r"^https://careers\.pathao\.com/jobs/\d+/?$",
        ),
        HtmlDetailSource(
            name="Cefalo Careers",
            organization_name="Cefalo",
            listing_urls=["https://career.cefalo.com/"],
            detail_url_regex=r"^https://career\.cefalo\.com/job/[^/]+/?$",
        ),
        HtmlDetailSource(
            name="ShopUp Careers",
            organization_name="ShopUp",
            listing_urls=["https://shopup.org/career"],
            detail_url_regex=r"^https://(?:www\.)?shopup\.org/job-postings/[^/]+/?$",
        ),

        # Public job portals. Official employer pages still win on duplicates.
        BdJobsSource(),
        BdJobsAcademicSource(),
        JobComBdSource(),
        NextJobzSource(),
        SearchDiscoverySource(),
    ]

    if include_demo:
        sources.append(DemoSource())

    return sources
