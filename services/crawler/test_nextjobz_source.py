from sources.nextjobz_source import NextJobzSource


def test_nextjobz_ai_title_is_relevant():
    assert NextJobzSource._relevant(
        "Junior Machine Learning Engineer",
        "Dhaka\n0 to 2 years",
    )


def test_nextjobz_cs_lecturer_is_relevant():
    assert NextJobzSource._relevant(
        "Lecturer",
        "Department of Computer Science and Engineering\nDhaka",
    )


def test_nextjobz_non_cs_lecturer_is_not_relevant():
    assert not NextJobzSource._relevant(
        "Lecturer",
        "Department of Political Science\nDhaka",
    )
