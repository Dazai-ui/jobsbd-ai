from sources.bdjobs_source import BdJobsSource
from sources.jobcombd_source import JobComBdSource


def test_bdjobs_job_id_parsing():
    assert BdJobsSource._job_id(
        "https://jobs.bdjobs.com/jobdetails/?id=1531485&ln=1"
    ) == "1531485"
    assert BdJobsSource._job_id(
        "https://bdjobs.com/h/details/1531485"
    ) == "1531485"


def test_bdjobs_title_prefilter():
    assert BdJobsSource._relevant_title("Junior Machine Learning Engineer")
    assert BdJobsSource._relevant_title("Data Analyst - Intern")
    assert not BdJobsSource._relevant_title("Senior DevOps Engineer")


def test_job_com_bd_job_id_parsing():
    assert JobComBdSource._job_id(
        "https://job.com.bd/jobs/details/?i=3474"
    ) == "3474"


def test_bdjobs_listing_context_and_company_fallback():
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(
        """
        <div class="job-card">
          <a href="/jobdetails/?id=1535918">Data Scientist (Credit-SME)</a>
          <div>IDLC Finance PLC</div>
          <div>Experience: At least 1 year</div>
          <div>Application Deadline: 5 Oct 2026</div>
          <div>Job Location: Dhaka</div>
        </div>
        """,
        "html.parser",
    )
    anchor = soup.find("a")
    context = BdJobsSource._card_text(anchor, "Data Scientist (Credit-SME)")
    lines = context.splitlines()
    assert "IDLC Finance PLC" in context
    assert BdJobsSource._organization(lines, "Data Scientist (Credit-SME)") == "IDLC Finance PLC"
