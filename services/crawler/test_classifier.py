from models import NormalizedJob
from classifier import enrich, accepted


def make(title, requirements=""):
    return NormalizedJob(
        title=title,
        organization_name="Test Org",
        source_name="Test",
        source_url="https://example.com",
        requirements=requirements,
    )


def test_junior_ml_is_accepted():
    job = enrich(make("Junior Machine Learning Engineer", "0-2 years experience"))
    assert job.is_ai_ml
    assert accepted(job)


def test_senior_ai_is_rejected():
    job = enrich(make("Senior AI Engineer", "Minimum 5 years of experience"))
    assert job.is_ai_ml
    assert not accepted(job)


def test_lecturer_is_accepted():
    job = enrich(make("Lecturer, Department of CSE"))
    assert job.is_academic
    assert job.academic_role == "lecturer"
    assert accepted(job)
