from sources.aiub_pdf_source import AiubFacultyPdfSource
from sources.nsu_source import NsuFacultySource


def test_nsu_detects_plain_lecturer_but_not_only_senior_lecturer():
    assert "Lecturer" in NsuFacultySource._roles(
        "Master's degree is required for Lecturer positions."
    )
    assert "Lecturer" not in NsuFacultySource._roles(
        "We are recruiting a Senior Lecturer."
    )


def test_aiub_detects_entry_roles_from_faculty_pdf_text():
    roles = AiubFacultyPdfSource._roles(
        "Lecturer\nAssistant Professor\nProfessor"
    )
    assert "Lecturer" in roles
    assert "Assistant Lecturer" not in roles
