from datetime import datetime
from fingerprint import make_fingerprint
from models import NormalizedJob


def job(source_name, source_url, source_job_id):
    return NormalizedJob(
        title="Junior ML Engineer",
        organization_name="ABC Ltd.",
        source_name=source_name,
        source_url=source_url,
        source_job_id=source_job_id,
        deadline=datetime(2026, 10, 20),
    )


def test_same_job_across_sources_has_same_fingerprint():
    a = job("Official", "https://abc.com/jobs/1", "1")
    b = job("Portal", "https://portal.example/job/99", "99")
    assert make_fingerprint(a) == make_fingerprint(b)


def test_same_job_different_source_urls_deduplicates():
    a = make("Junior Data Scientist")
    a.organization_name = "Acme Ltd."
    a.source_url = "https://company.example/jobs/123"
    a.source_job_id = "123"

    b = make("Junior Data Scientist")
    b.organization_name = "Acme Limited"
    b.source_url = "https://linkedin.com/jobs/view/999"
    b.source_job_id = "999"

    assert make_fingerprint(a) == make_fingerprint(b)
