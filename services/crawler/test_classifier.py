from datetime import datetime, timedelta, timezone

from models import NormalizedJob
from classifier import enrich, accepted


def make(title, requirements="", deadline=None):
    return NormalizedJob(
        title=title,
        organization_name="Test Org",
        source_name="Test",
        source_url="https://example.com",
        requirements=requirements,
        deadline=deadline,
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


def test_senior_lecturer_is_not_entry_academic():
    job = enrich(make("Senior Lecturer, Department of CSE"))
    assert not job.is_academic


def test_assistant_lecturer_is_accepted():
    job = enrich(make("Assistant Lecturer - CSE"))
    assert job.academic_role == "assistant_lecturer"
    assert accepted(job)


def test_non_cs_adjunct_faculty_is_rejected():
    job = enrich(make("Adjunct Faculty, Department of EEE"))
    assert job.academic_role == "adjunct_faculty"
    assert not accepted(job)


def test_cse_adjunct_faculty_is_accepted():
    job = enrich(make("Adjunct Faculty, Department of CSE"))
    assert job.academic_role == "adjunct_faculty"
    assert accepted(job)


def test_academic_role_with_more_than_two_years_is_rejected():
    job = enrich(make("Lecturer - CSE", "Minimum 3 years experience"))
    assert job.is_academic
    assert not accepted(job)


def test_expired_job_is_rejected():
    job = enrich(make(
        "Junior ML Engineer",
        "0-2 years experience",
        deadline=datetime.now(timezone.utc) - timedelta(days=1),
    ))
    assert not accepted(job)


def test_unknown_experience_senior_ai_role_is_rejected():
    job = enrich(make("Senior Data Scientist"))
    assert job.is_ai_ml
    assert not accepted(job)


def test_senior_named_ai_role_can_pass_if_experience_is_within_limit():
    job = enrich(make("Senior Data Scientist", "1-2 years experience"))
    assert accepted(job)


def test_non_cs_lecturer_is_rejected():
    job = enrich(make("Lecturer, Department of Political Science"))
    assert job.is_academic
    assert not accepted(job)


def test_cse_lecturer_is_accepted():
    job = enrich(make("Lecturer, Department of Computer Science and Engineering"))
    assert job.is_academic
    assert accepted(job)


def test_software_engineering_lecturer_is_accepted():
    job = enrich(make("Lecturer - Software Engineering"))
    assert job.is_academic
    assert accepted(job)


def test_ambiguous_faculty_role_without_cs_context_is_rejected():
    job = enrich(make("Adjunct Faculty"))
    assert job.is_academic
    assert not accepted(job)
