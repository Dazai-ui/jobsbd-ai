from sources.html_detail_source import HtmlDetailSource


def source():
    return HtmlDetailSource(
        name="Test Careers",
        organization_name="Test Org",
        listing_urls=["https://example.com/jobs/"],
        detail_url_regex=r"^https://example\.com/jobs/\d+/?$",
    )


def test_deadline_pathao_style():
    deadline = source()._extract_deadline(
        "We will be accepting applications till August 22, 2026\nJob Location: Dhaka"
    )
    assert deadline.year == 2026
    assert deadline.month == 8
    assert deadline.day == 22


def test_deadline_uiu_style():
    deadline = source()._extract_deadline(
        "Candidates would be required to apply online by September 15, 2026 (Tuesday)."
    )
    assert deadline.year == 2026
    assert deadline.month == 9
    assert deadline.day == 15


def test_metadata_labels():
    text = "Job Category: Fintech\nJob Type: Full Time\nJob Location: Dhaka"
    assert source()._extract_label(text, ("Job Location", "Location")) == "Dhaka"
    assert source()._extract_label(text, ("Job Type",)) == "Full Time"


def test_h3_heading_supported_for_du_style_pages():
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(
        "<h3>Lecturer, Department of CSE (02 post)</h3>",
        "html.parser",
    )
    assert source()._first_heading(soup) == "Lecturer, Department of CSE (02 post)"
