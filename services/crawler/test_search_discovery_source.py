from sources.search_discovery_source import SearchDiscoverySource


def test_search_discovery_allows_linkedin_job_urls():
    assert SearchDiscoverySource._allowed_url(
        "https://www.linkedin.com/jobs/view/1234567890/"
    )
    assert not SearchDiscoverySource._allowed_url(
        "https://www.linkedin.com/in/example/"
    )


def test_search_discovery_parses_linkedin_hiring_title():
    title, company = SearchDiscoverySource._parse_identity(
        "Acme hiring Junior Machine Learning Engineer in Dhaka | LinkedIn",
        "https://www.linkedin.com/jobs/view/1/",
    )
    assert title == "Junior Machine Learning Engineer"
    assert company == "Acme"
