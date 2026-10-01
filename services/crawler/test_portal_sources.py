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
