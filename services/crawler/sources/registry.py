from sources.aiub_pdf_source import AiubFacultyPdfSource
from sources.demo_source import DemoSource
from sources.ewu_pdf_source import EwuAcademicPdfSource
from sources.html_detail_source import HtmlDetailSource
from sources.nsu_source import NsuFacultySource
from sources.ulab_source import UlabFacultySource


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
    ]

    if include_demo:
        sources.append(DemoSource())

    return sources
