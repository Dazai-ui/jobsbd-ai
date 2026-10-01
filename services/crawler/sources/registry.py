from sources.demo_source import DemoSource
from sources.html_detail_source import HtmlDetailSource


def build_sources(include_demo: bool = False):
    sources = [
        HtmlDetailSource(
            name="UIU Careers",
            organization_name="United International University (UIU)",
            listing_urls=["https://www.uiu.ac.bd/career/"],
            detail_url_regex=r"^https://www\.uiu\.ac\.bd/career/(?!page/)(?!$)[^/]+/?$",
        ),
        HtmlDetailSource(
            name="Pathao Careers",
            organization_name="Pathao",
            listing_urls=["https://careers.pathao.com/job-openings/"],
            detail_url_regex=r"^https://careers\.pathao\.com/jobs/\d+/?$",
        ),
    ]

    if include_demo:
        sources.append(DemoSource())

    return sources
