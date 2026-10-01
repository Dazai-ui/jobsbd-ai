from bs4 import BeautifulSoup

from sources.ulab_source import UlabFacultySource


def test_ulab_extracts_only_entry_level_rows():
    html = """
    <table>
      <tr><th>School/ Department/Center</th><th>Position</th><th>Area</th></tr>
      <tr><td>CSE</td><td>Professor</td><td>AI</td></tr>
      <tr><td>CSE</td><td>Lecturer</td><td>Software Engineering</td></tr>
      <tr><td>EEE</td><td>Adjunct Faculty</td><td>Power</td></tr>
    </table>
    """
    rows = list(UlabFacultySource()._rows(BeautifulSoup(html, "html.parser")))
    assert rows == [
        ("Lecturer", "CSE", "Software Engineering"),
        ("Adjunct Faculty", "EEE", "Power"),
    ]


def test_ulab_deadline_parsing():
    deadline = UlabFacultySource._deadline(
        "Application deadline: August 10, 2026"
    )
    assert deadline.year == 2026
    assert deadline.month == 8
    assert deadline.day == 10
