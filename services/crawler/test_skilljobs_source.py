from sources.skilljobs_source import SkillJobsSource, TARGET_TITLE


def test_skilljobs_title_prefilter():
    assert TARGET_TITLE.search("Junior Machine Learning Engineer")
    assert TARGET_TITLE.search("Lecturer (Data Science), Department of Software Engineering")
    assert TARGET_TITLE.search("Research Assistant - AI Lab")
    assert not TARGET_TITLE.search("Area Sales Manager")


def test_skilljobs_expiration_date_parsing():
    deadline = SkillJobsSource._date(
        "Expiration date\nOctober 5, 2026",
        "deadline",
    )
    assert deadline.year == 2026
    assert deadline.month == 10
    assert deadline.day == 5
