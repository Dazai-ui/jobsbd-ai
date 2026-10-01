from sources.bdjobs_academic_source import (
    ACADEMIC_ROLE_RE,
    CS_CONTEXT_RE,
)


def test_bdjobs_academic_requires_entry_role():
    assert ACADEMIC_ROLE_RE.search("Lecturer (Department of CSE)")
    assert ACADEMIC_ROLE_RE.search("Research Assistant - Computer Science")
    assert not ACADEMIC_ROLE_RE.search("Assistant Professor, Department of CSE")


def test_bdjobs_academic_requires_cs_context():
    assert CS_CONTEXT_RE.search("Lecturer, Department of Computer Science and Engineering")
    assert CS_CONTEXT_RE.search("Lecturer - AI & Data Science")
    assert not CS_CONTEXT_RE.search("Lecturer, Department of Political Science")
