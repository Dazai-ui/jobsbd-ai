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
